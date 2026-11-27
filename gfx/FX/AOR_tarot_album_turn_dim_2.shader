# 牌册翻页：新一页的牌原地播一遍自带的翻牌帧（第 2 格，延迟 0.05 秒）。
# 用 A/B 两套按钮轮流启用，Disable→Up 重置 AnimationTime，动画每次翻页都重播（同议会表决弹窗）。
Includes = { "buttonstate.fxh" }
PixelShader = {
    Samplers = {
        MapTexture = {
            Index = 0
            MagFilter = "Linear"
            MinFilter = "Linear"
            MipFilter = "None"
            AddressU = "Clamp"
            AddressV = "Clamp"
        }
    }
}
VertexStruct VS_OUTPUT {
    float4 vPosition : PDX_POSITION;
    float2 vTexCoord : TEXCOORD0;
};
VertexShader = {
    MainCode VertexShader
    [[
        VS_OUTPUT main(const VS_INPUT v) {
            VS_OUTPUT Out;
            Out.vPosition = mul(WorldViewProjectionMatrix, float4(v.vPosition.xyz, 1));
            Out.vTexCoord = v.vTexCoord;
            return Out;
        }
    ]]
}
PixelShader = {
    MainCode PixelShaderTurn
    [[
        float4 main(VS_OUTPUT v) : PDX_COLOR {
            // 直接逐帧播 card_XX.dds 自带的 24 帧翻牌（牌背 → 牌面），比抽牌时的 48fps 快：0.30 秒播完
            float P = saturate((Time - AnimationTime - 0.050f) / 0.300f);
            float Frame = min(0.0f + floor(P * (24.0f - 0.0f)), 23.0f);
            float U = saturate(v.vTexCoord.x * 24.0f);
            float4 Tex = tex2D(MapTexture, float2((Frame + U) / 24.0f, v.vTexCoord.y)) * Color;
            float Grey = dot(Tex.rgb, float3(0.212671f, 0.715160f, 0.072169f)) * 0.55f;
            Tex.rgb = float3(Grey, Grey, Grey);
            return Tex;
        }
    ]]
    MainCode PixelShaderHidden
    [[
        float4 main(VS_OUTPUT v) : PDX_COLOR {
            return float4(0.0f, 0.0f, 0.0f, 0.0f);
        }
    ]]
}
BlendState BlendState {
    BlendEnable = yes
    SourceBlend = "src_alpha"
    DestBlend = "inv_src_alpha"
}
Effect Up { VertexShader = "VertexShader" PixelShader = "PixelShaderTurn" }
Effect Down { VertexShader = "VertexShader" PixelShader = "PixelShaderTurn" }
Effect Over { VertexShader = "VertexShader" PixelShader = "PixelShaderTurn" }
Effect Disable { VertexShader = "VertexShader" PixelShader = "PixelShaderHidden" }
