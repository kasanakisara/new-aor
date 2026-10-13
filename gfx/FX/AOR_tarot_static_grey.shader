# Reuse the final frame of the original 24-frame atlas; no new texture.
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
            // Sprite geometry is one frame wide. Ignore button-state Offset.
            Out.vTexCoord = v.vTexCoord;
            // Single front texture: no atlas offset.
            return Out;
        }
    ]]
}
PixelShader = {
    MainCode PixelShaderGrey
    [[
        float4 main(VS_OUTPUT v) : PDX_COLOR {
            float4 OutColor = tex2D(MapTexture, v.vTexCoord) * Color;
            float Grey = dot(OutColor.rgb, float3(0.212671f, 0.715160f, 0.072169f));
            OutColor.rgb = float3(Grey, Grey, Grey);
            return OutColor;
        }
    ]]
}
BlendState BlendState {
    BlendEnable = yes
    SourceBlend = "src_alpha"
    DestBlend = "inv_src_alpha"
}
Effect Up { VertexShader = "VertexShader" PixelShader = "PixelShaderGrey" }
Effect Down { VertexShader = "VertexShader" PixelShader = "PixelShaderGrey" }
Effect Over { VertexShader = "VertexShader" PixelShader = "PixelShaderGrey" }
Effect Disable { VertexShader = "VertexShader" PixelShader = "PixelShaderGrey" }
