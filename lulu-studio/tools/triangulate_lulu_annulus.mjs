import fs from 'node:fs';
import {ShapeUtils,Vector2} from 'three';
const data=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
const points=a=>a.map(p=>new Vector2(p[0],p[1]));
const result=ShapeUtils.triangulateShape(points(data.outer),[points(data.inner)]);
fs.writeFileSync(process.argv[3],JSON.stringify(result));
