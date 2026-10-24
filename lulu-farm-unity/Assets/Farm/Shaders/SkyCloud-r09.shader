Shader "LuluFarm/SkyCloud-r09"
{
 // O7 cloud sea: soft wrap lighting from the main light, bluish shade, no shadows; fog blends far puffs into the sky.
 Properties { _Lit("Lit",Color)=(0.98,0.99,1,1) _Shade("Shade",Color)=(0.74,0.82,0.91,1) }
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
 half4 _Lit; half4 _Shade;
 CBUFFER_END
 struct A {float4 p:POSITION;float3 n:NORMAL;}; struct V{float4 p:SV_POSITION;float3 n:TEXCOORD0;float fog:TEXCOORD1;};
 V vert(A v){V o;float3 w=TransformObjectToWorld(v.p.xyz);o.p=TransformWorldToHClip(w);o.n=TransformObjectToWorldNormal(v.n);o.fog=ComputeFogFactor(o.p.z);return o;}
 half4 frag(V i):SV_Target {
  Light l=GetMainLight();
  float3 n=normalize(i.n);
  half wrap=saturate(dot(n,l.direction)*.5+.5);
  half up=saturate(n.y*.5+.5);
  half3 c=lerp(_Shade.rgb,_Lit.rgb,saturate(wrap*.65+up*.45));
  return half4(MixFog(c,i.fog),1);
 }
 ENDHLSL
 }
 UsePass "Universal Render Pipeline/Lit/DepthOnly"
 }
}
