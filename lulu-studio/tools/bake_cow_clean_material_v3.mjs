// Separate v3 cow head material candidate. Originals and prior candidates stay intact.
// Use broad UV color context to distinguish markings from embedded bright scratches.
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import {createRequire} from 'node:module';
const require=createRequire(import.meta.url);
const sharp=require('/Users/haowen/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');

const inputFile=process.argv[2]||'public/models/animals-refined/v1/cow.glb';
const outputFile=process.argv[3]||'public/models/animal-studies/cow-head-clean-v3.glb';
assert.notEqual(path.resolve(inputFile),path.resolve(outputFile));
assert.ok(!/\/animals\/cow\.glb$/.test(path.resolve(outputFile)));
assert.ok(!/\/animals-refined\/v1\//.test(path.resolve(outputFile)));
const originalFile='public/models/animals/cow.glb';
const input=await fs.readFile(inputFile),original=await fs.readFile(originalFile);
function unpack(bytes) {
  const length=bytes.readUInt32LE(12);
  return {doc:JSON.parse(bytes.subarray(20,20+length)),binary:bytes.subarray(28+length,28+length+bytes.readUInt32LE(20+length))};
}
const {doc,binary}=unpack(input),source=unpack(original);
const primitive=doc.meshes[0].primitives[0],eyePrimitive=doc.meshes[0].primitives[1];
const body=doc.materials[primitive.material],eye=doc.materials[eyePrimitive.material];
const native=source.doc.materials[source.doc.meshes[0].primitives[0].material];
const baseIndex=native.pbrMetallicRoughness.baseColorTexture.index;
const normalIndex=native.normalTexture.index;
const mrIndex=native.pbrMetallicRoughness.metallicRoughnessTexture.index;
function imageBytes(textureIndex,from={doc,binary}) {
  const image=from.doc.images[from.doc.textures[textureIndex].source];
  const view=from.doc.bufferViews[image.bufferView];
  return from.binary.subarray(view.byteOffset||0,(view.byteOffset||0)+view.byteLength);
}
for(const index of [baseIndex,normalIndex,mrIndex]) assert.ok(imageBytes(index).equals(imageBytes(index,source)),'Original embedded texture resource must match');
function attribute(index) {
  const a=doc.accessors[index],v=doc.bufferViews[a.bufferView];
  const components={VEC3:3,VEC2:2,SCALAR:1}[a.type];
  const bytes={5126:4,5125:4,5123:2}[a.componentType];
  const values=new Float64Array(a.count*components);
  const offset=(v.byteOffset||0)+(a.byteOffset||0),stride=v.byteStride||components*bytes;
  for(let i=0;i<a.count;i++)for(let k=0;k<components;k++) {
    const at=offset+i*stride+k*bytes;
    values[i*components+k]=a.componentType===5126?binary.readFloatLE(at):a.componentType===5125?binary.readUInt32LE(at):binary.readUInt16LE(at);
  }
  return values;
}
const positions=attribute(primitive.attributes.POSITION),uv=attribute(primitive.attributes.TEXCOORD_0);
const base=await sharp(imageBytes(baseIndex)).removeAlpha().raw().toBuffer({resolveWithObject:true});
const context=await sharp(imageBytes(baseIndex)).removeAlpha().median(31).raw().toBuffer();
const width=base.info.width,height=base.info.height,count=width*height;
const spatial=new Float32Array(count),coverage=new Uint8Array(count),eyeMask=new Uint8Array(count);
function smooth(a,b,x){const t=Math.max(0,Math.min(1,(x-a)/(b-a)));return t*t*(3-2*t);}
const weights=new Float32Array(positions.length/3);
for(let i=0;i<weights.length;i++) {
  const y=positions[i*3+1],z=positions[i*3+2];
  weights[i]=Math.max(smooth(.05,.16,y)*smooth(.15,.37,z),smooth(.25,.39,y));
}
function raster(indices,isEye=false) {
  for(let k=0;k<indices.length;k+=3) {
    const ids=[indices[k],indices[k+1],indices[k+2]],xs=ids.map(i=>uv[i*2]*width),ys=ids.map(i=>uv[i*2+1]*height);
    const det=(ys[1]-ys[2])*(xs[0]-xs[2])+(xs[2]-xs[1])*(ys[0]-ys[2]);
    if(Math.abs(det)<1e-8)continue;
    const x0=Math.max(0,Math.floor(Math.min(...xs))),x1=Math.min(width-1,Math.ceil(Math.max(...xs)));
    const y0=Math.max(0,Math.floor(Math.min(...ys))),y1=Math.min(height-1,Math.ceil(Math.max(...ys)));
    for(let y=y0;y<=y1;y++)for(let x=x0;x<=x1;x++) {
      const u=((ys[1]-ys[2])*(x+.5-xs[2])+(xs[2]-xs[1])*(y+.5-ys[2]))/det;
      const v=((ys[2]-ys[0])*(x+.5-xs[2])+(xs[0]-xs[2])*(y+.5-ys[2]))/det,w=1-u-v;
      if(u<-.001||v<-.001||w<-.001)continue;
      const at=y*width+x;coverage[at]=1;
      if(isEye)eyeMask[at]=1;
      else spatial[at]=Math.max(spatial[at],u*weights[ids[0]]+v*weights[ids[1]]+w*weights[ids[2]]);
    }
  }
}
raster(attribute(primitive.indices));raster(attribute(eyePrimitive.indices),true);

// Separable O(n) rectangular morphology. Closing fills bright scratch holes and
// gaps inside the original black territory without depending on their color.
function extrema(input,radius,maximum) {
  const Type=input.constructor,tmp=new Type(count),out=new Type(count);
  const queue=new Int32Array(Math.max(width,height));
  function line(length,read,write) {
    let head=0,tail=0,next=0;
    for(let center=0;center<length;center++) {
      const right=Math.min(length-1,center+radius);
      for(;next<=right;next++) {
        const value=read(next);
        while(tail>head&&(maximum?read(queue[tail-1])<=value:read(queue[tail-1])>=value))tail--;
        queue[tail++]=next;
      }
      const left=center-radius;while(tail>head&&queue[head]<left)head++;
      write(center,read(queue[head]));
    }
  }
  for(let y=0;y<height;y++)line(width,x=>input[y*width+x],(x,v)=>tmp[y*width+x]=v);
  for(let x=0;x<width;x++)line(height,y=>tmp[y*width+x],(y,v)=>out[y*width+x]=v);
  return out;
}
const darkSeed=new Uint8Array(count),warmProtect=new Uint8Array(count),warmContext=new Uint8Array(count),darkContext=new Uint8Array(count);
for(let i=0;i<count;i++) {
  const k=i*3,r=base.data[k],g=base.data[k+1],b=base.data[k+2],hi=Math.max(r,g,b),lo=Math.min(r,g,b);
  const cr=context[k],cg=context[k+1],cb=context[k+2],ch=Math.max(cr,cg,cb),cl=Math.min(cr,cg,cb);
  // Original pixel color alone must never protect a warm/white scratch inside
  // the coat. Require a coherent broad marking in its local neighborhood.
  warmProtect[i]=(r>g+22||(hi>165&&lo>105))?1:0;
  warmContext[i]=(cr>cg+22&&cr>110)||(ch>175&&cl>105)?1:0;
  darkContext[i]=ch<130&&ch-cl<65?1:0;
  darkSeed[i]=hi<105&&hi-lo<55?1:0;
}
const closingRadius=24,gutterRadius=24,eyeGutter=6;
const closed=extrema(extrema(darkSeed,closingRadius,true),closingRadius,false);
const coherentWarm=extrema(warmContext,10,true);
const protectedEyes=extrema(eyeMask,eyeGutter,true);
let masks=new Float32Array(count),filledBright=0,changed=0,strong=0;
for(let i=0;i<count;i++) {
  if((!closed[i]&&!darkContext[i])||(warmProtect[i]&&coherentWarm[i])||protectedEyes[i])continue;
  masks[i]=spatial[i];
  if(spatial[i]>.5&&!darkSeed[i]&&Math.max(base.data[i*3],base.data[i*3+1],base.data[i*3+2])>=105)filledBright++;
}
// Expand only into unoccupied UV gutters, never into another occupied color area.
const expanded=extrema(masks,gutterRadius,true);
for(let i=0;i<count;i++) {
  // Unoccupied gutters belong to the neighboring cleaned island, even when
  // the old gutter pixels themselves were cream/gray-colored contamination.
  if(!coverage[i]&&!protectedEyes[i])masks[i]=expanded[i];
  if(masks[i]>.001){changed++;if(masks[i]>.95)strong++;}
}
assert.ok(changed>20000&&changed<count*.35,'Head cleanup must remain localized');
assert.ok(filledBright>100,'Contextual coat mask must actually include bright marks');
const target=[22,22,22];
for(let i=0;i<count;i++) {
  const m=masks[i];if(!m)continue;
  for(let c=0;c<3;c++)base.data[i*3+c]=Math.round(base.data[i*3+c]*(1-m)+target[c]*m);
}
const normal=await sharp(imageBytes(normalIndex)).removeAlpha().raw().toBuffer({resolveWithObject:true});
const mr=await sharp(imageBytes(mrIndex)).removeAlpha().raw().toBuffer({resolveWithObject:true});
const specular=Buffer.alloc(mr.info.width*mr.info.height*4,255);
function maskAt(x,y,w,h){return masks[Math.min(height-1,Math.floor((y+.5)*height/h))*width+Math.min(width-1,Math.floor((x+.5)*width/w))];}
for(let y=0;y<normal.info.height;y++)for(let x=0;x<normal.info.width;x++) {
  const m=maskAt(x,y,normal.info.width,normal.info.height);if(!m)continue;
  const k=(y*normal.info.width+x)*3;
  let nx=(normal.data[k]/255*2-1)*(1-m),ny=(normal.data[k+1]/255*2-1)*(1-m),nz=(normal.data[k+2]/255*2-1)*(1-m)+m;
  const len=Math.hypot(nx,ny,nz)||1;nx/=len;ny/=len;nz/=len;
  normal.data[k]=Math.round((nx+1)*127.5);normal.data[k+1]=Math.round((ny+1)*127.5);normal.data[k+2]=Math.round((nz+1)*127.5);
}
for(let y=0;y<mr.info.height;y++)for(let x=0;x<mr.info.width;x++) {
  const m=maskAt(x,y,mr.info.width,mr.info.height);if(!m)continue;
  const i=y*mr.info.width+x,k=i*3;mr.data[k+1]=Math.round(mr.data[k+1]*(1-m)+230*m);mr.data[k+2]=Math.round(mr.data[k+2]*(1-m));
  specular[i*4+3]=Math.round(255*(1-m*.85));
}
let payload=Buffer.from(binary);
function addMap(bytes,sourceTexture) {
  payload=Buffer.concat([payload,Buffer.alloc((4-payload.length%4)%4)]);
  const offset=payload.length;payload=Buffer.concat([payload,bytes]);
  const view=doc.bufferViews.length;doc.bufferViews.push({buffer:0,byteOffset:offset,byteLength:bytes.length});
  const image=doc.images.length;doc.images.push({bufferView:view,mimeType:'image/png'});
  const texture=doc.textures.length;doc.textures.push({...doc.textures[sourceTexture],source:image});return texture;
}
const textureIndexes=[];
for(const [map,sourceTexture] of [[base,baseIndex],[mr,mrIndex],[normal,normalIndex]]) {
  const encoded=await sharp(map.data,{raw:{width:map.info.width,height:map.info.height,channels:3}}).png().toBuffer();
  textureIndexes.push(addMap(encoded,sourceTexture));
}
const specularPNG=await sharp(specular,{raw:{width:mr.info.width,height:mr.info.height,channels:4}}).png().toBuffer();
const newSpecular=addMap(specularPNG,mrIndex);
body.pbrMetallicRoughness.baseColorTexture.index=textureIndexes[0];
body.pbrMetallicRoughness.metallicRoughnessTexture.index=textureIndexes[1];
body.normalTexture.index=textureIndexes[2];
body.extensions={...body.extensions,KHR_materials_specular:{specularFactor:1,specularTexture:{index:newSpecular,texCoord:0}}};
// The approved v1 eye response uses untouched original color/normal resources.
eye.pbrMetallicRoughness.baseColorTexture.index=baseIndex;eye.normalTexture.index=normalIndex;
const stats={method:'native UV material bake with broad 31px contextual coat/marking classification and closing',contextMedianSize:31,closingRadius,gutterRadius,eyeGutter,targetSRGB:target,changedPixels:changed,fullyCleanedPixels:strong,filledBrightPixels:filledBright,geometryUnchanged:true,visualAcceptance:'pending'};
doc.extras={...doc.extras,cowHeadCleanupV3:stats};
doc.buffers[0].byteLength=payload.length;
let json=Buffer.from(JSON.stringify(doc));json=Buffer.concat([json,Buffer.alloc((4-json.length%4)%4,32)]);
payload=Buffer.concat([payload,Buffer.alloc((4-payload.length%4)%4)]);
const header=Buffer.alloc(12);header.write('glTF');header.writeUInt32LE(2,4);header.writeUInt32LE(28+json.length+payload.length,8);
const jh=Buffer.alloc(8);jh.writeUInt32LE(json.length);jh.writeUInt32LE(0x4e4f534a,4);
const bh=Buffer.alloc(8);bh.writeUInt32LE(payload.length);bh.writeUInt32LE(0x004e4942,4);
const output=Buffer.concat([header,jh,json,bh,payload]);
await fs.mkdir(path.dirname(outputFile),{recursive:true});
await fs.writeFile(outputFile,output,{flag:'wx'});
console.log(JSON.stringify({file:outputFile,sha256:crypto.createHash('sha256').update(output).digest('hex'),bytes:output.length,...stats}));
