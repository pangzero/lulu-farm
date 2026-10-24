Shader "LuluFarm/SkyCloud-r09"
{
 // O7 cloud sea: soft wrap lighting from the main light, warm lit side, bluish shade, no shadows.
 // r10: slow world-space drift, and an optional own linear fog for horizon towers beyond Unity's 80 m fog end.
 Properties {
  _Lit("Lit",Color)=(1,0.973,0.933,1) _Shade("Shade",Color)=(0.66,0.75,0.86,1)
  _Drift("Drift (m)",Float)=0.6
  _OwnFog("Own fog (0 = Unity fog)",Float)=0 _OwnFogStart("Own fog start",Float)=70 _OwnFogEnd("Own fog end",Float)=190 _OwnFogColor("Own fog colour",Color)=(0.87,0.93,0.95,1)
 }
 SubShader {
 Tags { "RenderPipeline"="UniversalPipeline" "RenderType"="Opaque" "Queue"="Geometry" }
 Pass {
 Tags { "LightMode"="UniversalForward" }
 HLSLPROGRAM
 #pragma vertex vert
 #pragma fragment frag
 #pragma multi_compile_fog
 #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
 #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"
 CBUFFER_START(UnityPerMaterial)
 half4 _Lit; half4 _Shade; float _Drift; float _OwnFog; float _OwnFogStart; float _OwnFogEnd; half4 _OwnFogColor;
 CBUFFER_END
 struct A {float4 p:POSITION;float3 n:NORMAL;}; struct V{float4 p:SV_POSITION;float3 n:TEXCOORD0;float fog:TEXCOORD1;float dist:TEXCOORD2;};
 V vert(A v){
  V o;float3 w=TransformObjectToWorld(v.p.xyz);
  float t=_Time.y;
  w.xz+=float2(sin(t*.05+w.z*.03),cos(t*.04+w.x*.03))*_Drift;
  w.y+=sin(t*.07+w.x*.05+w.z*.04)*.25*_Drift;
  o.p=TransformWorldToHClip(w);o.n=TransformObjectToWorldNormal(v.n);o.fog=ComputeFogFactor(o.p.z);
  o.dist=distance(w,GetCameraPositionWS());return o;}
 half4 frag(V i):SV_Target {
  Light l=GetMainLight();
  float3 n=normalize(i.n);
  half wrap=saturate(dot(n,l.direction)*.5+.5);
  half up=saturate(n.y*.5+.5);
  half3 c=lerp(_Shade.rgb,_Lit.rgb,saturate(wrap*.65+up*.45));
  if(_OwnFog>.5) return half4(lerp(c,_OwnFogColor.rgb,saturate((i.dist-_OwnFogStart)/max(_OwnFogEnd-_OwnFogStart,1))),1);
  return half4(MixFog(c,i.fog),1);
 }
 ENDHLSL
 }
 UsePass "Universal Render Pipeline/Lit/DepthOnly"
 }
}
