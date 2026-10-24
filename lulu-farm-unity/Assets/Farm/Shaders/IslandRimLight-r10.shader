Shader "LuluFarm/IslandRimLight-r10"
{
 // O7 r10: a sunlit band on the last ~1.8 m of grass before the island edge. Drawn over the existing ground as a
 // proportional brighten (Blend DstColor One: result = ground x (1 + glow)), so shadows and pigment variation stay.
 // uv.y: 0 at the inner edge of the band, 1 at the rim.
 Properties { _Glow("Warm glow",Color)=(0.30,0.24,0.10,1) _Power("Falloff power",Float)=1.6 }
 SubShader {
 Tags { "RenderPipeline"="UniversalPipeline" "RenderType"="Transparent" "Queue"="Transparent-50" }
 Blend DstColor One ZWrite Off ZTest LEqual Cull Back Offset -1,-1
 Pass {
 Tags { "LightMode"="UniversalForward" }
 HLSLPROGRAM
 #pragma vertex vert
 #pragma fragment frag
 #pragma multi_compile_fog
 #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
 CBUFFER_START(UnityPerMaterial)
 half4 _Glow; float _Power;
 CBUFFER_END
 struct A {float4 p:POSITION;float2 uv:TEXCOORD0;}; struct V{float4 p:SV_POSITION;float2 uv:TEXCOORD0;float fog:TEXCOORD1;};
 V vert(A v){V o;o.p=TransformObjectToHClip(v.p.xyz);o.uv=v.uv;o.fog=ComputeFogFactor(o.p.z);return o;}
 half4 frag(V i):SV_Target {
  half3 c=_Glow.rgb*pow(saturate(i.uv.y),_Power);
  return half4(MixFogColor(c,half3(0,0,0),i.fog),1);
 }
 ENDHLSL
 }
 }
}
