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
			float2 L = float2( frac( v.vTexCoord.x * 3.0f ), v.vTexCoord.y );
			float2 Px = L * float2( 292.0f, 92.0f );
			if( Px.x < 3.0f || Px.x > 292.0f - 3.0f || Px.y < 3.0f || Px.y > 92.0f - 3.0f )
			{
				return float4( Tex.rgb, Tex.a * 1.0f ) * Color;
			}
			float2 A = ( Px - 3.0f ) / float2( 292.0f - 6.0f, 92.0f - 6.0f );
			float2 HK = float2( 12.9898f, 78.233f );
			float Lum = dot( Tex.rgb, float3( 0.299f, 0.587f, 0.114f ) );
			// 褪色：黑不死、白不透
			Lum = 0.06f + Lum * 0.84f;
			// 纯黑白（用户不要棕褐泛黄）
			float3 C = float3( Lum, Lum, Lum );
			// 镜头暗角（横条画面，竖向更强）
			float2 Q = ( A - 0.5f ) * float2( 1.1f, 1.7f );
			C *= 1.0f - 0.42f * saturate( dot( Q, Q ) * 1.25f );
			// 胶片颗粒（固定，不闪）
			float2 Pi = floor( Px );
			float G = frac( sin( dot( Pi, HK ) ) * 43758.5453f );
			float G2 = frac( sin( dot( floor( Pi * 0.5f ), HK + 3.1f ) ) * 24634.6345f );
			C += ( G * 0.6f + G2 * 0.4f - 0.5f ) * 0.075f;
			// 零星灰尘点（不画竖划痕：用户试过，像两条白线）
			float2 Cell = floor( Px / 23.0f );
			float D = frac( sin( dot( Cell, HK * 1.7f ) ) * 43758.5453f );
			if( D > 0.93f )
			{
				float2 Dp = Cell * 23.0f + 23.0f * float2( frac( D * 37.0f ), frac( D * 91.0f ) );
				float2 Dd = Px - Dp;
				if( dot( Dd, Dd ) < 1.3f ) { C = lerp( C, float3( 0.88f, 0.88f, 0.88f ), 0.55f ); }
			}
			return float4( saturate( C ), Tex.a * 1.0f ) * Color;
		}
	]]

	MainCode PixelShaderDisable
	[[
		float4 main( VS_OUTPUT v ) : PDX_COLOR
		{
			float4 Tex = tex2D( MapTexture, v.vTexCoord );
			float2 L = float2( frac( v.vTexCoord.x * 3.0f ), v.vTexCoord.y );
			float2 Px = L * float2( 292.0f, 92.0f );
			if( Px.x < 3.0f || Px.x > 292.0f - 3.0f || Px.y < 3.0f || Px.y > 92.0f - 3.0f )
			{
				return float4( Tex.rgb, Tex.a * 0.40f ) * Color;
			}
			float2 A = ( Px - 3.0f ) / float2( 292.0f - 6.0f, 92.0f - 6.0f );
			float2 HK = float2( 12.9898f, 78.233f );
			float Lum = dot( Tex.rgb, float3( 0.299f, 0.587f, 0.114f ) );
			// 褪色：黑不死、白不透
			Lum = 0.06f + Lum * 0.84f;
			// 纯黑白（用户不要棕褐泛黄）
			float3 C = float3( Lum, Lum, Lum );
			// 镜头暗角（横条画面，竖向更强）
			float2 Q = ( A - 0.5f ) * float2( 1.1f, 1.7f );
			C *= 1.0f - 0.42f * saturate( dot( Q, Q ) * 1.25f );
			// 胶片颗粒（固定，不闪）
			float2 Pi = floor( Px );
			float G = frac( sin( dot( Pi, HK ) ) * 43758.5453f );
			float G2 = frac( sin( dot( floor( Pi * 0.5f ), HK + 3.1f ) ) * 24634.6345f );
			C += ( G * 0.6f + G2 * 0.4f - 0.5f ) * 0.075f;
			// 零星灰尘点（不画竖划痕：用户试过，像两条白线）
			float2 Cell = floor( Px / 23.0f );
			float D = frac( sin( dot( Cell, HK * 1.7f ) ) * 43758.5453f );
			if( D > 0.93f )
			{
				float2 Dp = Cell * 23.0f + 23.0f * float2( frac( D * 37.0f ), frac( D * 91.0f ) );
				float2 Dd = Px - Dp;
				if( dot( Dd, Dd ) < 1.3f ) { C = lerp( C, float3( 0.88f, 0.88f, 0.88f ), 0.55f ); }
			}
			return float4( saturate( C ), Tex.a * 0.40f ) * Color;
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
