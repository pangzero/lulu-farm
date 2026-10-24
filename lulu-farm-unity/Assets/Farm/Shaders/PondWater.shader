Shader "LuluFarm/PondWater"
{
 Properties { _Shallow("Shallow blue",Color)=(0.20,0.66,0.80,1) _Deep("Deep blue",Color)=(0.12,0.49,0.68,1) }
 SubShader {
 Tags { "RenderPipeline"="UniversalPipeline" "RenderType"="Opaque" "Queue"="Geometry" }
 Pass {
 Tags { "LightMode"="UniversalForward" }
 HLSLPROGRAM
 #pragma vertex vert
 #pragma fragment frag
 #pragma multi_compile_fog
 #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
 CBUFFER_START(UnityPerMaterial)
 half4 _Shallow; half4 _Deep;
 CBUFFER_END
 struct A {float4 p:POSITION;}; struct V{float4 p:SV_POSITION;float3 w:TEXCOORD0;float fog:TEXCOORD1;};
 V vert(A v){V o;o.w=TransformObjectToWorld(v.p.xyz);o.p=TransformWorldToHClip(o.w);o.fog=ComputeFogFactor(o.p.z);return o;}
 half4 frag(V i):SV_Target { float2 q=i.w.xz;float wave=sin(q.x*3.3+sin(q.y*2.1)+_Time.y*.6)*sin(q.y*3.1-q.x*.35+_Time.y*.4);half3 c=lerp(_Deep.rgb,_Shallow.rgb,.58+wave*.13);float glint=pow(saturate(wave),14)*.10;c+=glint;return half4(MixFog(c,i.fog),1);}
 ENDHLSL
 }
 UsePass "Universal Render Pipeline/Lit/DepthOnly"
 }
}
