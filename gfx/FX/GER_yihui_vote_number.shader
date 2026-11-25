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
			float Code = floor( Offset.x * 4.0f + 0.5f );
			float Side = floor( Code / 1000.0f );
			float Final = Code - Side * 1000.0f;
			float T = Time - AnimationTime - 0.600f;
			float P = saturate( T * 14.0f / 26.0f );
			P = P * P * ( 3.0f - 2.0f * P );
			float Cur = floor( Final * P + 0.0001f );
			float Hun = floor( Cur / 100.0f );
			float Ten = floor( Cur / 10.0f ) - Hun * 10.0f;
			float One = Cur - Hun * 100.0f - Ten * 10.0f;
			float Nd = 1.0f;
			if( Cur > 9.5f ) { Nd = 2.0f; }
			if( Cur > 99.5f ) { Nd = 3.0f; }
			float X = v.vTexCoord.x * 12.0f;
			float Cell = floor( X );
			float Frac = X - Cell;
			float Idx = Cell;
			if( Side < 1.5f )
			{
				if( Cell < 3.0f - Nd ) { return float4( 0.0f, 0.0f, 0.0f, 0.0f ); }
			}
			else
			{
				if( Cell > Nd - 0.5f ) { return float4( 0.0f, 0.0f, 0.0f, 0.0f ); }
				Idx = Cell + 3.0f - Nd;
			}
			float D = One;
			if( Idx < 0.5f ) { D = Hun; }
			else if( Idx < 1.5f ) { D = Ten; }
			float4 Glyph = tex2D( MapTexture, float2( ( D + Frac ) / 12.0f, v.vTexCoord.y ) );
			float3 Col = float3( 0.000f, 0.624f, 0.012f );
			if( Side > 1.5f ) { Col = float3( 1.000f, 0.196f, 0.196f ); }
			return float4( Col * Glyph.r, Glyph.a ) * Color;
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
