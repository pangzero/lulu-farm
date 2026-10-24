Shader "LuluFarm/FabricUV"
{
 Properties { _BaseMap("Fabric atlas UV1",2D)="white" {} _BaseColor("Tint",Color)=(1,1,1,1) }
 SubShader {
 Tags { "RenderPipeline"="UniversalPipeline" "RenderType"="Opaque" "Queue"="Geometry" }
 Pass {
 Tags { "LightMode"="UniversalForward" }
 HLSLPROGRAM
 #pragma vertex vert
 #pragma fragment frag
 #pragma multi_compile _ _MAIN_LIGHT_SHADOWS _MAIN_LIGHT_SHADOWS_CASCADE _MAIN_LIGHT_SHADOWS_SCREEN
 #pragma multi_compile_fragment _ _SHADOWS_SOFT
 #pragma multi_compile_fog
 #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
 #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"
 TEXTURE2D(_BaseMap); SAMPLER(sampler_BaseMap);
 CBUFFER_START(UnityPerMaterial)
 float4 _BaseMap_ST; half4 _BaseColor;
 CBUFFER_END
 struct A { float4 pos:POSITION; float3 normal:NORMAL; float2 fabric:TEXCOORD1; };
 struct V { float4 pos:SV_POSITION; float3 world:TEXCOORD0; float3 normal:TEXCOORD1; float2 uv:TEXCOORD2; float fog:TEXCOORD3; };
 V vert(A v) { V o; o.world=TransformObjectToWorld(v.pos.xyz); o.pos=TransformWorldToHClip(o.world);o.normal=TransformObjectToWorldNormal(v.normal);o.uv=TRANSFORM_TEX(v.fabric,_BaseMap);o.fog=ComputeFogFactor(o.pos.z);return o; }
 half4 frag(V i):SV_Target { half3 n=normalize(i.normal);Light l=GetMainLight(TransformWorldToShadowCoord(i.world));half3 albedo=SAMPLE_TEXTURE2D(_BaseMap,sampler_BaseMap,i.uv).rgb*_BaseColor.rgb;half3 rgb=albedo*(SampleSH(n)+l.color*saturate(dot(n,l.direction))*l.shadowAttenuation*l.distanceAttenuation);return half4(MixFog(rgb,i.fog),1); }
 ENDHLSL
 }
 UsePass "Universal Render Pipeline/Lit/ShadowCaster"
 UsePass "Universal Render Pipeline/Lit/DepthOnly"
 }
}
