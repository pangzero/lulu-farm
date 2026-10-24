Shader "LuluFarm/SkyBirds-r10"
{
 // O7 r10: small white birds circling the sky island. Every bird is a few triangles; the vertex shader puts it on an
 // elliptical orbit, faces it along its velocity and flaps the wings in bursts with glides between. Driven by
 // _FarmR07Time, so pause, motion switch and fixed captures behave like the other r07 ambient motion.
 // uv0: x = flap weight (0 body .. 1 wing tip), y = side (-1/1). uv1: orbit radius, height, angular speed, phase.
 // uv2: orbit centre x, z, bob amplitude, flap rate. uv3: x = scale.
 Properties { _Lit("Lit",Color)=(0.99,0.98,0.95,1) _Shade("Shade",Color)=(0.70,0.76,0.84,1) }
 SubShader {
 Tags { "RenderPipeline"="UniversalPipeline" "RenderType"="Opaque" "Queue"="Geometry" }
 Cull Off
 Pass {
 Tags { "LightMode"="UniversalForward" }
 HLSLPROGRAM
 #pragma vertex vert
 #pragma fragment frag
 #pragma multi_compile_fog
 #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
 #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"
 CBUFFER_START(UnityPerMaterial)
 half4 _Lit; half4 _Shade;
 CBUFFER_END
 float _FarmR07Time;
 struct A {float4 p:POSITION;float2 uv0:TEXCOORD0;float4 uv1:TEXCOORD1;float4 uv2:TEXCOORD2;float4 uv3:TEXCOORD3;};
 struct V{float4 p:SV_POSITION;float3 n:TEXCOORD0;float fog:TEXCOORD1;};
 V vert(A v){
  V o; float t=_FarmR07Time;
  float r=v.uv1.x, h=v.uv1.y, w=v.uv1.z, ph=v.uv1.w;
  float a=ph+t*w;
  float3 pos=float3(v.uv2.x+cos(a)*r, h+sin(t*.4+ph*3)*v.uv2.z, v.uv2.y+sin(a)*r*.8);
  float3 fwd=normalize(float3(-sin(a)*r*w, 0, cos(a)*r*.8*w)+1e-5);
  float3 up=float3(0,1,0);
  float3 right=normalize(cross(up,fwd));
  float glide=smoothstep(-.2,.4,sin(t*.35+ph*6.1));
  float theta=(sin(t*v.uv2.w+ph*5)*.55*glide+.12)*v.uv0.x;
  float side=v.uv0.y, d=abs(v.p.x);
  float lx=v.p.x, ly=v.p.y;
  if(v.uv0.x>0){lx=side*d*cos(theta);ly=v.p.y+d*sin(theta);}
  float s=v.uv3.x;
  float3 w3=pos+right*lx*s+up*ly*s+fwd*v.p.z*s;
  o.p=TransformWorldToHClip(w3);
  o.n=normalize(-right*side*sin(theta)+up*cos(theta));
  o.fog=ComputeFogFactor(o.p.z);
  return o;}
 half4 frag(V i, FRONT_FACE_TYPE facing:FRONT_FACE_SEMANTIC):SV_Target {
  Light l=GetMainLight();
  float3 n=normalize(i.n)*IS_FRONT_VFACE(facing,1,-1);
  half3 c=lerp(_Shade.rgb,_Lit.rgb,saturate(dot(n,l.direction)*.5+.5));
  return half4(MixFog(c,i.fog),1);
 }
 ENDHLSL
 }
 }
}
