Shader "LuluFarm/Waterfall-r09"
{
 // O7 sky-island waterfall: opaque (no transparency sorting against clouds), unlit, scrolling streaks.
 // uv.x runs across the fall 0..1, uv.y is metres below the lip.
 Properties { _Water("Water",Color)=(0.56,0.84,0.95,1) _Foam("Foam",Color)=(0.95,0.99,1,1) _Speed("Fall speed (m/s)",Float)=2.4 }
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
 CBUFFER_START(UnityPerMaterial)
 half4 _Water; half4 _Foam; float _Speed;
 CBUFFER_END
 float _FarmR07Time;   // r07 ambient clock (FarmAmbientR07): pauses with the game, 0 in fixed captures
 struct A {float4 p:POSITION;float2 uv:TEXCOORD0;}; struct V{float4 p:SV_POSITION;float2 uv:TEXCOORD0;float fog:TEXCOORD1;};
 V vert(A v){V o;o.p=TransformObjectToHClip(v.p.xyz);o.uv=v.uv;o.fog=ComputeFogFactor(o.p.z);return o;}
 half4 frag(V i):SV_Target {
  float x=i.uv.x, y=i.uv.y, t=_FarmR07Time*_Speed;
  float lane=floor(x*9.0);
  float offset=frac(sin(lane*12.9898)*43758.5453);
  float streak=frac((y-t)*.45+offset);
  float band=smoothstep(0,.12,streak)*smoothstep(.55,.25,streak);
  float lip=smoothstep(.5,0,y);
  float side=smoothstep(.12,0,min(x,1-x));
  half3 c=lerp(_Water.rgb,_Foam.rgb,saturate(band*.5+lip*.75+side*.45));
  return half4(MixFog(c,i.fog),1);
 }
 ENDHLSL
 }
 }
}
