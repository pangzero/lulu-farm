// Bake the native cow material's dark-head cleanup, preserving the UV layout.
// This is a deterministic 3D material-data bake, not a generated replacement image.
import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
const require=createRequire(import.meta.url);
const sharp=require('/Users/haowen/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');

const file=process.argv[2];
const input=await fs.readFile(file);
const jsonLength=input.readUInt32LE(12);
const doc=JSON.parse(input.subarray(20,20+jsonLength));
const binary=input.subarray(28+jsonLength,28+jsonLength+input.readUInt32LE(20+jsonLength));
const primitive=doc.meshes[0].primitives[0];
const eyePrimitive=doc.meshes[0].primitives[1];
function attribute(index) {
  const a=doc.accessors[index],v=doc.bufferViews[a.bufferView];
  const components={VEC3:3,VEC2:2,SCALAR:1}[a.type];
  const bytes={5126:4,5125:4,5123:2}[a.componentType];
  const values=new Float64Array(a.count*components);
  const offset=(v.byteOffset||0)+(a.byteOffset||0),stride=v.byteStride||components*bytes;
  for(let i=0;i<a.count;i++) for(let k=0;k<components;k++) {
    const at=offset+i*stride+k*bytes;
    values[i*components+k]=a.componentType===5126?binary.readFloatLE(at):a.componentType===5125?binary.readUInt32LE(at):binary.readUInt16LE(at);
  }
  return values;
}
const positions=attribute(primitive.attributes.POSITION),uv=attribute(primitive.attributes.TEXCOORD_0);
function imageBytes(textureIndex) {
  const image=doc.images[doc.textures[textureIndex].source],v=doc.bufferViews[image.bufferView];
  return binary.subarray(v.byteOffset||0,(v.byteOffset||0)+v.byteLength);
}
const body=doc.materials[primitive.material],eye=doc.materials[eyePrimitive.material];
const baseIndex=body.pbrMetallicRoughness.baseColorTexture.index;
const normalIndex=body.normalTexture.index;
const mrIndex=body.pbrMetallicRoughness.metallicRoughnessTexture.index;
const baseBytes=imageBytes(baseIndex);
const base=await sharp(baseBytes).removeAlpha().raw().toBuffer({resolveWithObject:true});
const median=await sharp(baseBytes).removeAlpha().median(7).raw().toBuffer();
const width=base.info.width,height=base.info.height;
assert.equal(base.info.channels,3);
const spatial=new Float32Array(width*height),protect=new Uint8Array(width*height);
function smooth(a,b,x) {const t=Math.max(0,Math.min(1,(x-a)/(b-a)));return t*t*(3-2*t);}
const weights=new Float32Array(positions.length/3);
for(let i=0;i<weights.length;i++) {
  const y=positions[i*3+1],z=positions[i*3+2];
  weights[i]=Math.max(smooth(.05,.16,y)*smooth(.15,.37,z),smooth(.25,.39,y));
}
function raster(indices,eyeRegion=false) {
  for(let k=0;k<indices.length;k+=3) {
    const ids=[indices[k],indices[k+1],indices[k+2]];
    if(!eyeRegion&&ids.every(i=>weights[i]===0))continue;
    const x=ids.map(i=>uv[i*2]*width),y=ids.map(i=>uv[i*2+1]*height);
    const det=(y[1]-y[2])*(x[0]-x[2])+(x[2]-x[1])*(y[0]-y[2]);
    if(Math.abs(det)<1e-8)continue;
    const x0=Math.max(0,Math.floor(Math.min(...x))),x1=Math.min(width-1,Math.ceil(Math.max(...x)));
    const y0=Math.max(0,Math.floor(Math.min(...y))),y1=Math.min(height-1,Math.ceil(Math.max(...y)));
    for(let py=y0;py<=y1;py++)for(let px=x0;px<=x1;px++) {
      const u=((y[1]-y[2])*(px+.5-x[2])+(x[2]-x[1])*(py+.5-y[2]))/det;
      const v=((y[2]-y[0])*(px+.5-x[2])+(x[0]-x[2])*(py+.5-y[2]))/det;
      const w=1-u-v;
      if(u<-.001||v<-.001||w<-.001)continue;
      const at=py*width+px;
      if(eyeRegion)protect[at]=1;
      else spatial[at]=Math.max(spatial[at],u*weights[ids[0]]+v*weights[ids[1]]+w*weights[ids[2]]);
    }
  }
}
raster(attribute(primitive.indices));raster(attribute(eyePrimitive.indices),true);
// Extend the bake into the texture gutters so UV island filtering cannot bring
// the old scratch-colored pixels back as thin seam lines.
for(let pass=0;pass<2;pass++) {
  const expanded=new Float32Array(spatial);
  for(let y=1;y<height-1;y++)for(let x=1;x<width-1;x++) {
    const i=y*width+x,v=spatial[i];if(!v)continue;
    expanded[i-1]=Math.max(expanded[i-1],v);expanded[i+1]=Math.max(expanded[i+1],v);
    expanded[i-width]=Math.max(expanded[i-width],v);expanded[i+width]=Math.max(expanded[i+width],v);
  }
  spatial.set(expanded);
}
// Preserve the entire eye footprint plus a small filtering gutter.
const eyePoints=[];for(let i=0;i<protect.length;i++)if(protect[i])eyePoints.push(i);
for(const at of eyePoints) {
  const x=at%width,y=Math.floor(at/width);
  for(let dy=-3;dy<=3;dy++)for(let dx=-3;dx<=3;dx++) {
    const nx=x+dx,ny=y+dy;if(nx>=0&&nx<width&&ny>=0&&ny<height)spatial[ny*width+nx]=0;
  }
}
const masks=new Float32Array(spatial.length);
let changed=0,strong=0;
for(let i=0;i<spatial.length;i++) {
  if(spatial[i]===0)continue;
  const k=i*3,r=base.data[k],g=base.data[k+1],b=base.data[k+2];
  // Keep pink inner ears, tan horns, and the warm cream blaze explicitly.
  const mr=median[k],mg=median[k+1],mb=median[k+2];
  if(mr>mg+22||(Math.max(r,g,b)>165&&Math.max(r,g,b)-Math.min(r,g,b)>22))continue;
  const neutral=1-smooth(25,60,Math.max(mr,mg,mb)-Math.min(mr,mg,mb));
  const darkness=1-smooth(65,150,Math.max(mr,mg,mb));
  const mask=spatial[i]*neutral*darkness;
  if(mask<=.001)continue;
  masks[i]=mask;changed++;if(mask>.95)strong++;
  for(let c=0;c<3;c++)base.data[k+c]=Math.round(base.data[k+c]*(1-mask)+24*mask);
}
const normal=await sharp(imageBytes(normalIndex)).removeAlpha().raw().toBuffer({resolveWithObject:true});
const mr=await sharp(imageBytes(mrIndex)).removeAlpha().raw().toBuffer({resolveWithObject:true});
const specular=Buffer.alloc(mr.info.width*mr.info.height*4,255);
function maskAt(x,y,w,h) {return masks[Math.min(height-1,Math.floor((y+.5)*height/h))*width+Math.min(width-1,Math.floor((x+.5)*width/w))];}
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
assert.ok(changed>20000&&changed<width*height*.3,'Cow head material mask must remain local');
const encoded=[];
for(const map of [base,mr,normal])encoded.push(await sharp(map.data,{raw:{width:map.info.width,height:map.info.height,channels:3}}).png().toBuffer());
let payload=Buffer.from(binary);
function addMap(bytes,sourceTexture) {
  const pad=Buffer.alloc((4-payload.length%4)%4);payload=Buffer.concat([payload,pad]);
  const offset=payload.length;payload=Buffer.concat([payload,bytes]);
  const view=doc.bufferViews.length;doc.bufferViews.push({buffer:0,byteOffset:offset,byteLength:bytes.length});
  const image=doc.images.length;doc.images.push({bufferView:view,mimeType:'image/png'});
  const texture=doc.textures.length;doc.textures.push({...doc.textures[sourceTexture],source:image});
  return texture;
}
const newBase=addMap(encoded[0],baseIndex),newMR=addMap(encoded[1],mrIndex),newNormal=addMap(encoded[2],normalIndex);
const specularPNG=await sharp(specular,{raw:{width:mr.info.width,height:mr.info.height,channels:4}}).png().toBuffer();
const newSpecular=addMap(specularPNG,mrIndex);
body.pbrMetallicRoughness.baseColorTexture.index=newBase;
body.pbrMetallicRoughness.metallicRoughnessTexture.index=newMR;
body.normalTexture.index=newNormal;
body.extensions={...body.extensions,KHR_materials_specular:{specularFactor:1,specularTexture:{index:newSpecular,texCoord:0}}};
eye.pbrMetallicRoughness.baseColorTexture.index=newBase;eye.normalTexture.index=newNormal;
doc.buffers[0].byteLength=payload.length;
doc.extras.cowHeadCleanup={method:'UV-space native material bake',pixels:changed,fullyCleanedPixels:strong,protected:'iris-pupil catchlights, pink inner ears, cream blaze, horns',targetSRGB:[24,24,24]};
let json=Buffer.from(JSON.stringify(doc));json=Buffer.concat([json,Buffer.alloc((4-json.length%4)%4,32)]);
payload=Buffer.concat([payload,Buffer.alloc((4-payload.length%4)%4)]);
const header=Buffer.alloc(12);header.write('glTF');header.writeUInt32LE(2,4);header.writeUInt32LE(28+json.length+payload.length,8);
const jh=Buffer.alloc(8);jh.writeUInt32LE(json.length);jh.writeUInt32LE(0x4e4f534a,4);
const bh=Buffer.alloc(8);bh.writeUInt32LE(payload.length);bh.writeUInt32LE(0x004e4942,4);
await fs.writeFile(file,Buffer.concat([header,jh,json,bh,payload]));
console.log(JSON.stringify({changed_pixels:changed,fully_cleaned_pixels:strong,cow_head_texture_baked:true}));
