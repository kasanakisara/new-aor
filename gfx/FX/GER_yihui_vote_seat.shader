Includes = {
	"buttonstate.fxh"
}

PixelShader =
{
	Samplers =
	{
		MapTexture =
		{
			Index = 0
			MagFilter = "Linear"
			MinFilter = "Linear"
			MipFilter = "None"
			AddressU = "Clamp"
			AddressV = "Clamp"
			MipMapLodBias = -0.8
		}
		MaskTexture =
		{
			Index = 1
			MagFilter = "Linear"
			MinFilter = "Linear"
			MipFilter = "None"
			AddressU = "Clamp"
			AddressV = "Clamp"
		}
		AnimatedTexture =
		{
			Index = 2
			MagFilter = "Linear"
			MinFilter = "Linear"
			MipFilter = "None"
			AddressU = "Wrap"
			AddressV = "Wrap"
		}
		MaskTexture2 =
		{
			Index = 3
			MagFilter = "Linear"
			MinFilter = "Linear"
			MipFilter = "None"
			AddressU = "Clamp"
			AddressV = "Clamp"
		}
		AnimatedTexture2 =
		{
			Index = 4
			MagFilter = "Linear"
			MinFilter = "Linear"
			MipFilter = "None"
			AddressU = "Wrap"
			AddressV = "Wrap"
		}
		MaskingTexture =
		{
			Index = 5
			MagFilter = "Point"
			MinFilter = "Point"
			MipFilter = "None"
			AddressU = "Clamp"
			AddressV = "Clamp"
		}
	}
}

VertexStruct VS_OUTPUT
{
	float4  vPosition : PDX_POSITION;
	float2  vTexCoord : TEXCOORD0;
@ifdef ANIMATED
	float4  vAnimatedTexCoord : TEXCOORD1;
@endif
@ifdef MASKING
	float2  vMaskingTexCoord : TEXCOORD2;
@endif
};

VertexShader =
{
	MainCode VertexShader
	[[
		VS_OUTPUT main(const VS_INPUT v )
		{
			VS_OUTPUT Out;
			Out.vPosition  = mul( WorldViewProjectionMatrix, float4( v.vPosition.xyz, 1 ) );
			Out.vTexCoord = v.vTexCoord;
			Out.vTexCoord += Offset;
			return Out;
		}
	]]
}

PixelShader =
{
	MainCode PixelShaderUp
	[[
		float4 main( VS_OUTPUT v ) : PDX_COLOR
		{
			float4 Tex = tex2D( MapTexture, v.vTexCoord );
			float Code = floor( Offset.x * 128.0f + 0.5f );
			float Vote = floor( Code / 32.0f );
			float Batch = Code - Vote * 32.0f;
			float T = Time - AnimationTime - 0.600f;
			float Start = Batch / 14.0f;
			if( Vote < 0.5f || T < Start )
			{
				return float4( 0.0f, 0.0f, 0.0f, 0.0f );
			}
			float3 Col = float3( 0.361f, 0.612f, 0.275f );
			if( Vote > 1.5f ) { Col = float3( 0.722f, 0.243f, 0.212f ); }
			if( Vote > 2.5f ) { Col = float3( 0.518f, 0.518f, 0.486f ); }
			float3 Dot = Col * Tex.r;
			float DotA = Tex.b;
			if( T < Start + 1.0f / 14.0f )
			{
				float Glow = Tex.g * 0.6f;
				float A = max( DotA, Glow );
				float3 GlowCol = float3( 1.0f, 0.94f, 0.78f );
				float3 Mixed = ( GlowCol * Glow * ( 1.0f - DotA ) + Dot * DotA ) / max( A, 0.001f );
				return float4( Mixed, A ) * Color;
			}
			return float4( Dot, DotA ) * Color;
		}
	]]

	MainCode PixelShaderDisable
	[[
		float4 main( VS_OUTPUT v ) : PDX_COLOR
		{
			return float4( 0.0f, 0.0f, 0.0f, 0.0f );
		}
	]]
}

BlendState BlendState
{
	BlendEnable = yes
	SourceBlend = "src_alpha"
	DestBlend = "inv_src_alpha"
}

Effect Up
{
	VertexShader = "VertexShader"
	PixelShader = "PixelShaderUp"
}

Effect Down
{
	VertexShader = "VertexShader"
	PixelShader = "PixelShaderUp"
}

Effect Disable
{
	VertexShader = "VertexShader"
	PixelShader = "PixelShaderDisable"
}

Effect Over
{
	VertexShader = "VertexShader"
	PixelShader = "PixelShaderUp"
}
