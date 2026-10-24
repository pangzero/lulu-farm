#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <vector>
#include <string>
#include <map>
#include <cmath>
#include <cstring>
#include "Simplify.h"
// in: nv nt target agg | float p[nv*3] | int t[nt*3] | int locked[nv]
int main(int argc,char**argv){
  FILE*f=fopen(argv[1],"rb");int nv,nt,target;double agg;
  fread(&nv,4,1,f);fread(&nt,4,1,f);fread(&target,4,1,f);fread(&agg,8,1,f);
  std::vector<float>P(nv*3);std::vector<int>T(nt*3),L(nv);
  fread(P.data(),4,nv*3,f);fread(T.data(),4,nt*3,f);fread(L.data(),4,nv,f);fclose(f);
  Simplify::vertices.clear();Simplify::triangles.clear();
  for(int i=0;i<nv;i++){Simplify::Vertex v;v.p.x=P[i*3];v.p.y=P[i*3+1];v.p.z=P[i*3+2];v.locked=L[i];Simplify::vertices.push_back(v);}
  for(int i=0;i<nt;i++){Simplify::Triangle t;t.v[0]=T[i*3];t.v[1]=T[i*3+1];t.v[2]=T[i*3+2];t.attr=0;t.material=0;Simplify::triangles.push_back(t);}
  Simplify::simplify_mesh(target,agg,getenv("QV")!=0);{int nb=0,nl=0;for(auto&v:Simplify::vertices){nb+=v.border;nl+=v.locked;}fprintf(stderr,"border %d locked %d\n",nb,nl);}
  FILE*o=fopen(argv[2],"wb");int ov=Simplify::vertices.size(),ot=Simplify::triangles.size();
  fwrite(&ov,4,1,o);fwrite(&ot,4,1,o);
  for(auto&v:Simplify::vertices){float q[3]={(float)v.p.x,(float)v.p.y,(float)v.p.z};fwrite(q,4,3,o);}
  for(auto&t:Simplify::triangles)fwrite(t.v,4,3,o);
  fclose(o);return 0;}
