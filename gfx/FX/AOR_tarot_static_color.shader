# Always sample the final face of the existing 24-frame atlas.
# Dynamic image replacement can reset an icon's frame; select the UV here.
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
            // Single front texture: no atlas offset.
            return Out;
        }
    ]]
}
PixelShader = {
    MainCode PixelShaderColor
    [[
        float4 main(VS_OUTPUT v) : PDX_COLOR {
            return tex2D(MapTexture, v.vTexCoord) * Color;
        }
    ]]
}
BlendState BlendState {
    BlendEnable = yes
    SourceBlend = "src_alpha"
    DestBlend = "inv_src_alpha"
}
Effect Up { VertexShader = "VertexShader" PixelShader = "PixelShaderColor" }
Effect Down { VertexShader = "VertexShader" PixelShader = "PixelShaderColor" }
Effect Over { VertexShader = "VertexShader" PixelShader = "PixelShaderColor" }
Effect Disable { VertexShader = "VertexShader" PixelShader = "PixelShaderColor" }
