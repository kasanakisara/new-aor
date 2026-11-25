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
			float2 HK = float2( 12.9898f, 78.233f );

			// ---- 显影 ----
			float Lum = dot( Tex.rgb, float3( 0.299f, 0.587f, 0.114f ) );
			float2 Gp = v.vTexCoord * float2( 23.0f, 8.0f );
			float2 Gi = floor( Gp );
			float2 Gf = frac( Gp );
			Gf = Gf * Gf * ( 3.0f - 2.0f * Gf );
			float H00 = frac( sin( dot( Gi, HK ) ) * 43758.5453f );
			float H10 = frac( sin( dot( Gi + float2( 1.0f, 0.0f ), HK ) ) * 43758.5453f );
			float H01 = frac( sin( dot( Gi + float2( 0.0f, 1.0f ), HK ) ) * 43758.5453f );
			float H11 = frac( sin( dot( Gi + float2( 1.0f, 1.0f ), HK ) ) * 43758.5453f );
			float Blot = lerp( lerp( H00, H10, Gf.x ), lerp( H01, H11, Gf.x ), Gf.y );
			float Start = 0.62f * Lum + 0.16f * ( Blot - 0.5f );
			float P = saturate( ( Time - AnimationTime ) / 1.0f );
			float Dv = saturate( ( P * 1.25f - Start ) / 0.38f );
			Dv = Dv * Dv * ( 3.0f - 2.0f * Dv );
			float3 Sepia = saturate( float3( Lum * 1.07f + 0.04f, Lum * 0.93f + 0.03f, Lum * 0.74f + 0.01f ) );
			float3 Mono = lerp( float3( 0.965f, 0.945f, 0.890f ), Sepia, Dv );
			float Cv = saturate( ( P - 0.72f ) / 0.28f );
			Cv = Cv * Cv * ( 3.0f - 2.0f * Cv );
			float3 Col = lerp( Mono, Tex.rgb, Cv );

			// ---- 老胶片 ----
			float Fr = floor( Time * 15.0f );
			float Seed = frac( Fr * 0.6180339f ) * 97.0f;
			float Rnd = frac( sin( Seed * 12.9898f ) * 43758.5453f );
			Col *= 1.0f + 0.03f * sin( Time * 5.0f ) + 0.04f * ( Rnd - 0.5f );
			float L2 = dot( Col, float3( 0.299f, 0.587f, 0.114f ) );
			Col = lerp( float3( L2, L2, L2 ), Col, 0.78f );
			float2 Px = floor( v.vTexCoord * float2( 552.0f, 192.0f ) );
			float Grain = frac( sin( dot( Px + float2( Seed, Seed * 1.7f ), HK ) ) * 43758.5453f );
			Col = Col * 0.92f + Grain * 0.086f;
			float2 Q = ( v.vTexCoord - 0.5f ) * float2( 1.25f, 1.9f );
			Col *= 1.0f - 0.35f * saturate( dot( Q, Q ) * 1.4f );
			float Rs = frac( sin( Seed * 3.731f ) * 43758.5453f );
			if( Rs < 0.3f )
			{
				float Sx = 0.04f + 0.92f * frac( sin( Seed * 7.919f ) * 43758.5453f );
				if( abs( v.vTexCoord.x - Sx ) * 552.0f < 0.7f ) { Col = float3( 0.82f, 0.80f, 0.75f ); }
			}
			float Rd = frac( sin( Seed * 5.113f ) * 43758.5453f );
			if( Rd < 0.2f )
			{
				float2 Dp = float2( frac( sin( Seed * 9.271f ) * 43758.5453f ), frac( sin( Seed * 4.437f ) * 43758.5453f ) );
				float2 Dd = ( v.vTexCoord - Dp ) * float2( 552.0f, 192.0f );
				if( dot( Dd, Dd ) < 4.0f ) { Col = float3( 0.16f, 0.15f, 0.13f ); }
			}
			return float4( saturate( Col ), Tex.a ) * Color;
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
