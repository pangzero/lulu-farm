// Cow v4 candidate: native solid material on conservative head/ear interiors.
// No image generation, no UV morphology, no geometry edits, no prior file overwrite.
import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import {createRequire} from 'node:module';
const require=createRequire(import.meta.url);
const sharp=require('/Users/haowen/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
const inputFile='public/models/animals-refined/v1/cow.glb';
const originalFile='public/models/animals/cow.glb';
const outputFile='public/models/animal-studies/cow-head-clean-v4.glb';
const bytes=await fs.readFile(inputFile),sourceBytes=await fs.readFile(originalFile);
function unpack(b){const n=b.readUInt32LE(12);return {doc:JSON.parse(b.subarray(20,20+n)),binary:b.subarray(28+n,28+n+b.readUInt32LE(20+n))};}
const {doc,binary}=unpack(bytes),source=unpack(sourceBytes);
const body=doc.meshes[0].primitives[0],eye=doc.meshes[0].primitives[1];
function attribute(index) {
  const a=doc.accessors[index],view=doc.bufferViews[a.bufferView],c={SCALAR:1,VEC2:2,VEC3:3}[a.type],size={5126:4,5125:4,5123:2}[a.componentType];
  const values=new Float64Array(a.count*c),offset=(view.byteOffset||0)+(a.byteOffset||0),stride=view.byteStride||c*size;
  for(let i=0;i<a.count;i++)for(let j=0;j<c;j++) {
    const at=offset+i*stride+j*size;
    values[i*c+j]=a.componentType===5126?binary.readFloatLE(at):a.componentType===5125?binary.readUInt32LE(at):binary.readUInt16LE(at);
  }
  return values;
}
const positions=attribute(body.attributes.POSITION),uv=attribute(body.attributes.TEXCOORD_0),indices=attribute(body.indices),eyeIndices=attribute(eye.indices);
const originalMaterial=source.doc.materials[source.doc.meshes[0].primitives[0].material];
const texture=source.doc.textures[originalMaterial.pbrMetallicRoughness.baseColorTexture.index],image=source.doc.images[texture.source],view=source.doc.bufferViews[image.bufferView];
const albedoBytes=source.binary.subarray(view.byteOffset||0,(view.byteOffset||0)+view.byteLength);
const original=await sharp(albedoBytes).removeAlpha().raw().toBuffer({resolveWithObject:true});
const context=await sharp(albedoBytes).removeAlpha().median(31).raw().toBuffer();
const width=original.info.width,height=original.info.height;
function sample(map,u,v) {
  const x=Math.max(0,Math.min(width-1,Math.floor(u*width))),y=Math.max(0,Math.min(height-1,Math.floor(v*height))),k=(y*width+x)*3;
  return [map[k],map[k+1],map[k+2]];
}
function dark(c){return Math.max(...c)<130&&Math.max(...c)-Math.min(...c)<65;}
function bright(c){return Math.max(...c)>165&&Math.min(...c)>105;}
function pink(c){return c[0]>140&&c[0]>c[1]+38&&c[0]>c[2]+30;}
const vertexCount=positions.length/3,weldOf=new Uint32Array(vertexCount),lookup=new Map(),weldPositions=[];
for(let i=0;i<vertexCount;i++) {
  const p=[positions[i*3],positions[i*3+1],positions[i*3+2]],key=p.map(v=>Math.round(v*1e6)).join(',');
  let id=lookup.get(key);if(id===undefined){id=weldPositions.length;lookup.set(key,id);weldPositions.push(p);}weldOf[i]=id;
}
const n=weldPositions.length,neighbors=Array.from({length:n},()=>new Set()),darkVotes=new Uint32Array(n),brightVotes=new Uint32Array(n),pinkVotes=new Uint32Array(n),votes=new Uint32Array(n),eligible=new Uint8Array(n),protectedNode=new Uint8Array(n);
for(let i=0;i<vertexCount;i++) {
  const id=weldOf[i],color=sample(context,uv[i*2],uv[i*2+1]);votes[id]++;
  if(dark(color))darkVotes[id]++;if(bright(color))brightVotes[id]++;if(pink(color))pinkVotes[id]++;
}
for(let k=0;k<indices.length;k+=3) {
  const ids=[weldOf[indices[k]],weldOf[indices[k+1]],weldOf[indices[k+2]]];
  for(let i=0;i<3;i++){neighbors[ids[i]].add(ids[(i+1)%3]);neighbors[ids[(i+1)%3]].add(ids[i]);}
  // Face-center color gives UV seam vertices context from the actual surface.
  const u=(uv[indices[k]*2]+uv[indices[k+1]*2]+uv[indices[k+2]*2])/3;
  const v=(uv[indices[k]*2+1]+uv[indices[k+1]*2+1]+uv[indices[k+2]*2+1])/3;
  const color=sample(context,u,v);
  for(const id of ids){votes[id]++;if(dark(color))darkVotes[id]++;if(bright(color))brightVotes[id]++;if(pink(color))pinkVotes[id]++;}
}
let seed=new Uint8Array(n),cream=new Uint8Array(n),pinkCount=0,hornCount=0;
for(let i=0;i<n;i++) {
  const [x,y,z]=weldPositions[i];
  eligible[i]=(y>.25||(y>.13&&z>.45))?1:0;
  seed[i]=eligible[i]&&darkVotes[i]/Math.max(1,votes[i])>=.55?1:0;
  cream[i]=brightVotes[i]/Math.max(1,votes[i])>.65?1:0;
  // Horn tips/shafts are outside the target black head region.
  if(y>.53&&Math.abs(x)<.36){protectedNode[i]=1;hornCount++;}
  if(pinkVotes[i]/Math.max(1,votes[i])>.35){protectedNode[i]=1;pinkCount++;}
}
function morph(input,steps,dilate) {
  let current=input;
  for(let step=0;step<steps;step++) {
    const out=new Uint8Array(n);
    for(let i=0;i<n;i++) {
      if(!eligible[i])continue;
      let value=!!current[i];
      for(const j of neighbors[i]) {
        if(dilate&&current[j]){value=true;break;}
        if(!dilate&&!current[j]){value=false;break;}
      }
      out[i]=value?1:0;
    }
    current=out;
  }
  return current;
}
const closeSteps=7;
let closed=morph(morph(seed,closeSteps,true),closeSteps,false);
// Preserve coherent broad cream patches; narrow isolated seam lines can close.
let creamProtected=0;
for(let i=0;i<n;i++)if(cream[i]) {
  let total=1,same=1;
  for(const j of neighbors[i]){total++;same+=cream[j];}
  if(same/total>.80){protectedNode[i]=1;creamProtected++;}
}
// Keep the approved eye footprint plus a two-ring skin boundary unchanged.
let eyeNodes=new Uint8Array(n);for(const index of eyeIndices)eyeNodes[weldOf[index]]=1;
eyeNodes=morph(eyeNodes,2,true);
for(let i=0;i<n;i++)if(protectedNode[i]||eyeNodes[i])closed[i]=0;
// One extra graph erosion is the conservative boundary guard. Every selected
// triangle must have three vertices inside that guarded black territory.
const interior=morph(closed,1,false),solid=[],textured=[];
let repairedNodes=0;
for(let i=0;i<n;i++)if(interior[i]&&!seed[i])repairedNodes++;
for(let k=0;k<indices.length;k+=3) {
  const ids=[indices[k],indices[k+1],indices[k+2]];
  const target=ids.every(id=>interior[weldOf[id]])?solid:textured;target.push(...ids);
}
assert.ok(solid.length>3000&&solid.length<indices.length*.55,'Solid material must be a local head/ear interior');
assert.equal(solid.length+textured.length,indices.length);
let payload=Buffer.from(binary);
function addIndices(values) {
  const data=Buffer.alloc(values.length*4);values.forEach((value,i)=>data.writeUInt32LE(value,i*4));
  payload=Buffer.concat([payload,Buffer.alloc((4-payload.length%4)%4)]);const offset=payload.length;payload=Buffer.concat([payload,data]);
  const bufferView=doc.bufferViews.length;doc.bufferViews.push({buffer:0,byteOffset:offset,byteLength:data.length,target:34963});
  let minimum=Infinity,maximum=-Infinity;for(const value of values){minimum=Math.min(minimum,value);maximum=Math.max(maximum,value);}
  const accessor=doc.accessors.length;doc.accessors.push({bufferView,componentType:5125,count:values.length,type:'SCALAR',min:[minimum],max:[maximum]});return accessor;
}
const srgb=24/255,linear=((srgb+.055)/1.055)**2.4,solidMaterial=doc.materials.length;
doc.materials.push({name:'cow_black_head_interior_v4',pbrMetallicRoughness:{baseColorFactor:[linear,linear,linear,1],metallicFactor:0,roughnessFactor:.90},doubleSided:true,extensions:{KHR_materials_specular:{specularFactor:.15}}});
doc.extensionsUsed=[...new Set([...(doc.extensionsUsed||[]),'KHR_materials_specular'])];
doc.meshes[0].primitives=[{...body,indices:addIndices(textured)},eye,{...body,indices:addIndices(solid),material:solidMaterial}];
const stats={method:'welded-vertex graph closing and conservative solid-black interior face assignment',source:'v1 cow with original albedo median31 classification',closeSteps,interiorBoundaryRings:1,weldedVertices:n,solidTriangles:solid.length/3,texturedBodyTriangles:textured.length/3,repairedNodes,pinkProtectedNodes:pinkCount,hornProtectedNodes:hornCount,creamProtectedNodes:creamProtected,targetSRGB:24,targetLinear:linear,geometryPositionsNormalsUVsUnchanged:true,visualAcceptance:'pending'};
doc.extras={...doc.extras,cowHeadCleanupV4:stats};doc.buffers[0].byteLength=payload.length;
let json=Buffer.from(JSON.stringify(doc));json=Buffer.concat([json,Buffer.alloc((4-json.length%4)%4,32)]);payload=Buffer.concat([payload,Buffer.alloc((4-payload.length%4)%4)]);
const header=Buffer.alloc(12);header.write('glTF');header.writeUInt32LE(2,4);header.writeUInt32LE(28+json.length+payload.length,8);
const jh=Buffer.alloc(8);jh.writeUInt32LE(json.length);jh.writeUInt32LE(0x4e4f534a,4);const bh=Buffer.alloc(8);bh.writeUInt32LE(payload.length);bh.writeUInt32LE(0x004e4942,4);
const output=Buffer.concat([header,jh,json,bh,payload]);await fs.writeFile(outputFile,output,{flag:'wx'});
console.log(JSON.stringify({file:outputFile,bytes:output.length,sha256:crypto.createHash('sha256').update(output).digest('hex'),...stats}));
