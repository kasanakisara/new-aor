//------------------------------------------------------------------------------------
// AuroraEffect.shader -- Part of AuroraEffect
//
// Copyright (C) 2026 CzXieDdan. All rights reserved.
// 
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU Affero General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
// 
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU Affero General Public License for more details.
// 
// You should have received a copy of the GNU Affero General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.
//
// https://github.com/czxieddan/AuroraEffect
//------------------------------------------------------------------------------------
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
	}
}

VertexStruct VS_OUTPUT
{
	float4 vPosition : PDX_POSITION;
	float2 vTexCoord : TEXCOORD0;
};

VertexShader =
{
	MainCode VertexShader
	[[
		VS_OUTPUT main( const VS_INPUT v )
		{
			VS_OUTPUT Out;
			Out.vPosition = mul( WorldViewProjectionMatrix, float4( v.vPosition.xyz, 1.0f ) );
			Out.vTexCoord = v.vTexCoord;
			return Out;
		}
	]]
}

PixelShader =
{
	Code
	[[
		static const float TAU = 6.28318530f;
		static const float LOOP_TIME = 16.0f;

		float GetLoopPhase()
		{
			return frac( Time / LOOP_TIME ) * TAU;
		}

		float Hash12( float2 p )
		{
			return frac( sin( dot( p, float2( 127.1f, 311.7f ) ) ) * 43758.5453f );
		}

		float ValueNoise( float2 p )
		{
			float2 i = floor( p );
			float2 f = frac( p );
			float2 u = f * f * ( 3.0f - 2.0f * f );

			float a = Hash12( i );
			float b = Hash12( i + float2( 1.0f, 0.0f ) );
			float c = Hash12( i + float2( 0.0f, 1.0f ) );
			float d = Hash12( i + float2( 1.0f, 1.0f ) );

			return lerp( lerp( a, b, u.x ), lerp( c, d, u.x ), u.y );
		}

		float2 GetDomeCoord( float2 uv )
		{
			float y = saturate( uv.y );
			float widen = lerp( 0.90f, 1.76f, pow( y, 1.06f ) );
			return float2( ( uv.x - 0.5f ) * widen * 2.0f, y );
		}

		float GetHorizonLine( float x, float phase )
		{
			float horizon = 0.989f;
			horizon += 0.0016f * sin( x * 2.0f + phase );
			horizon += 0.0008f * sin( x * 6.1f - 1.7f );
			return horizon;
		}

		float GetStarLayer( float2 uv, float phase, float2 density, float threshold, float glowPower, float brightness, float seed )
		{
			float2 grid = uv * density + float2( seed * 17.0f, seed * 31.0f );
			float2 cell = floor( grid );
			float2 local = frac( grid ) - 0.5f;
			float rnd = Hash12( cell + float2( seed, seed * 2.0f ) );
			float starMask = smoothstep( threshold, 0.999998f, rnd );

			float phaseOffset = rnd * TAU + seed * 5.7f;
			float freqSlow = 0.55f + frac( rnd * 13.0f ) * 1.25f;
			float freqMid = 1.40f + frac( rnd * 29.0f ) * 2.60f;
			float freqFast = 3.20f + frac( rnd * 53.0f ) * 6.80f;

			float slow = 0.5f + 0.5f * sin( phase * freqSlow + phaseOffset );
			float mid = 0.5f + 0.5f * sin( phase * freqMid + phaseOffset * 1.37f + sin( phase + phaseOffset ) );
			float fast = 0.5f + 0.5f * sin( phase * freqFast + phaseOffset * 2.11f );

			float burst = pow( mid, 9.0f ) * ( 0.30f + 0.70f * fast );
			float sparkle = pow( fast, 16.0f );
			float twinkle = saturate( 0.14f + slow * 0.24f + mid * 0.20f + burst * 0.44f + sparkle * 0.40f );

			float starCore = exp( -dot( local, local ) * glowPower );
			float starHalo = exp( -dot( local, local ) * glowPower * 0.22f );
			float starShape = starCore * 0.60f + starHalo * 0.40f;
			return starMask * starShape * twinkle * brightness;
		}

		float GetStarField( float2 uv, float phase )
		{
			float dust = GetStarLayer( uv, phase, float2( 520.0f, 300.0f ), 0.9888f, 120.0f, 0.14f, 0.17f );
			float fine = GetStarLayer( uv, phase, float2( 390.0f, 224.0f ), 0.9918f, 84.0f, 0.22f, 1.43f );
			float mid = GetStarLayer( uv, phase, float2( 270.0f, 154.0f ), 0.9948f, 54.0f, 0.34f, 2.61f );
			float bright = GetStarLayer( uv, phase, float2( 156.0f, 90.0f ), 0.9974f, 26.0f, 0.50f, 3.87f );
			float rare = GetStarLayer( uv, phase, float2( 92.0f, 54.0f ), 0.9986f, 12.0f, 0.74f, 5.21f );
			float altitude = 1.0f - smoothstep( 0.92f, 1.02f, uv.y );
			return ( dust + fine + mid + bright + rare ) * altitude;
		}

		float GetHighHaze( float2 dome, float2 uv, float phase )
		{
			float2 driftA = float2( cos( phase ), sin( phase ) ) * 0.42f;
			float2 driftB = float2( cos( phase * 2.0f + 1.7f ), sin( phase * 2.0f + 1.7f ) ) * 0.24f;
			float hazeA = ValueNoise( float2( dome.x * 0.70f, uv.y * 1.28f ) * 2.2f + driftA + float2( 3.8f, 6.1f ) );
			float hazeB = ValueNoise( float2( dome.x * 1.18f, uv.y * 0.96f ) * 4.4f + driftB + float2( -2.7f, 1.4f ) );
			float haze = lerp( hazeA, hazeB, 0.30f );
			haze = smoothstep( 0.42f, 0.78f, haze );
			haze *= 1.0f - smoothstep( 0.26f, 0.92f, uv.y );
			return haze;
		}

		float3 GetNightSky( float2 uv, float2 dome, float phase )
		{
			float3 zenith = float3( 0.020f, 0.022f, 0.054f );
			float3 upper = float3( 0.036f, 0.038f, 0.078f );
			float3 lower = float3( 0.076f, 0.058f, 0.088f );

			float gradA = smoothstep( 0.08f, 0.72f, uv.y );
			float gradB = smoothstep( 0.56f, 0.96f, uv.y );
			float3 color = lerp( zenith, upper, gradA );
			color = lerp( color, lower, gradB * 0.66f );

			float haze = GetHighHaze( dome, uv, phase );
			float star = GetStarField( uv, phase );
			float vignette = 1.0f - 0.12f * saturate( pow( abs( dome.x ) / 1.92f, 1.35f ) );
			float zenithLift = exp( -pow( ( uv.y - 0.05f ) / 0.22f, 2.0f ) ) * exp( -pow( dome.x / 1.16f, 2.0f ) );

			color += float3( 0.016f, 0.012f, 0.024f ) * haze * 0.68f;
			color += float3( 0.38f, 0.39f, 0.60f ) * star * 1.82f;
			color += float3( 0.010f, 0.012f, 0.024f ) * zenithLift * 0.72f;
			color *= vignette;
			return color;
		}

		float4 RenderRedAurora( float2 uv, float2 dome, float phase )
		{
			float x = dome.x;
			float horizon = GetHorizonLine( x, phase );
			float sway =
				0.28f * sin( phase ) +
				0.16f * sin( phase * 2.0f + x ) +
				0.08f * sin( phase * 4.0f - x * 1.8f );
			float xFlow = x + sway;

			float top = 0.48f + 0.13f * xFlow * xFlow;
			top += 0.050f * sin( xFlow * 1.95f - phase * 2.0f );
			top += 0.028f * sin( xFlow * 5.20f + phase * 3.0f );

			float envelope = smoothstep( top - 0.15f, top + 0.05f, uv.y );

			float2 driftA = float2( cos( phase ), sin( phase ) ) * 0.94f;
			float2 driftB = float2( cos( phase * 2.0f + 1.3f ), sin( phase * 2.0f + 1.3f ) ) * 0.58f;
			float2 driftC = float2( cos( phase * 4.0f + 2.7f ), sin( phase * 4.0f + 2.7f ) ) * 0.32f;

			float cloudLarge = ValueNoise( float2( xFlow * 0.86f, uv.y * 1.02f ) * 2.8f + driftA + float2( 5.4f, 1.8f ) );
			float cloudMid = ValueNoise( float2( xFlow * 1.62f, uv.y * 0.92f ) * 5.2f + driftB + float2( -1.9f, 6.5f ) );
			float cloudFine = ValueNoise( float2( xFlow * 2.80f, uv.y * 1.20f ) * 7.6f + driftC + float2( 2.6f, -4.3f ) );
			float plume = smoothstep( 0.08f, 0.90f, cloudLarge * 0.46f + cloudMid * 0.38f + cloudFine * 0.16f );

			float warp = ( cloudLarge - 0.5f ) * 0.44f + ( cloudMid - 0.5f ) * 0.22f + ( cloudFine - 0.5f ) * 0.08f;
			float motionBand = 0.80f + 0.20f * sin( xFlow * 2.6f - phase * 3.0f + cloudLarge * 2.2f );
			float veilWide = 0.62f + 0.38f * pow( abs( sin( ( xFlow + warp ) * 5.6f - phase * 4.0f ) ), 0.66f );
			float veilFine = 0.74f + 0.26f * pow( abs( sin( ( xFlow + warp ) * 17.0f + uv.y * 5.0f + phase * 6.0f ) ), 1.75f );
			float veils = motionBand * lerp( 1.0f, veilWide * veilFine, 0.34f );

			float lobeLeft = exp( -pow( ( xFlow + 0.90f ) / 0.56f, 2.0f ) );
			float lobeMid = exp( -pow( ( xFlow - 0.01f ) / 0.64f, 2.0f ) );
			float lobeRight = exp( -pow( ( xFlow - 1.00f ) / 0.74f, 2.0f ) );
			float lobe = lobeLeft * 0.60f + lobeMid * 1.00f + lobeRight * 0.66f;

			float lowerGlow = exp( -pow( ( uv.y - 0.86f ) / 0.21f, 2.0f ) );
			float midGlow = exp( -pow( ( uv.y - 0.73f ) / 0.26f, 2.0f ) );
			float centerPillar = exp( -pow( xFlow / 0.26f, 2.0f ) ) * exp( -pow( ( uv.y - 0.78f ) / 0.18f, 2.0f ) );
			float horizonBloom = exp( -pow( ( uv.y - ( horizon - 0.012f ) ) / 0.14f, 2.0f ) ) * exp( -pow( xFlow / 1.65f, 2.0f ) );

			float density = envelope * ( 0.50f + 0.50f * plume ) * veils;
			float glow = envelope * ( lowerGlow * 0.68f + midGlow * 0.32f ) * ( 0.68f + 0.32f * lobe );
			float hot = density * ( 0.28f + 0.72f * lobe ) + centerPillar * 0.94f + horizonBloom * 0.34f;

			float3 deepRed = float3( 0.20f, 0.020f, 0.050f );
			float3 brightRed = float3( 0.98f, 0.10f, 0.23f );
			float3 pink = float3( 1.00f, 0.35f, 0.48f );
			float3 ember = float3( 0.60f, 0.05f, 0.11f );

			float colorMix = saturate( 0.28f + 0.60f * hot );
			float pinkMix = saturate( centerPillar * 0.24f + hot * 0.11f );

			float3 color = lerp( deepRed, brightRed, colorMix );
			color = lerp( color, pink, pinkMix );
			color += ember * glow * 0.20f;
			color *= glow * 0.96f + density * 1.00f;

			float alpha = saturate( glow + density * 0.36f + horizonBloom * 0.12f );
			return float4( color, alpha );
		}

		float4 ComposeAurora( float2 uv )
		{
			float phase = GetLoopPhase();
			float2 dome = GetDomeCoord( uv );
			float3 sky = GetNightSky( uv, dome, phase );
			float4 redAurora = RenderRedAurora( uv, dome, phase );

			float horizonLine = GetHorizonLine( dome.x, phase );
			float horizonGlow = exp( -pow( ( uv.y - ( horizonLine - 0.010f ) ) / 0.13f, 2.0f ) ) * exp( -pow( dome.x / 1.88f, 2.0f ) );
			float upperRedHaze = exp( -pow( ( uv.y - 0.64f ) / 0.32f, 2.0f ) ) * exp( -pow( dome.x / 1.62f, 2.0f ) ) * redAurora.a;

			sky += float3( 0.18f, 0.024f, 0.056f ) * horizonGlow * 0.50f;
			sky += float3( 0.13f, 0.018f, 0.042f ) * upperRedHaze * 0.24f;

			float3 color = sky + redAurora.rgb;

			float groundFade = smoothstep( horizonLine, horizonLine + 0.003f, uv.y );
			color = lerp( color, float3( 0.012f, 0.010f, 0.014f ), groundFade );

			return float4( saturate( color ), 1.0f );
		}
	]]

	MainCode PixelShaderAurora
	[[
		float4 main( VS_OUTPUT v ) : PDX_COLOR
		{
			float2 uv = saturate( v.vTexCoord );
			float4 aurora = ComposeAurora( uv );
			aurora.rgb *= Color.rgb;
			aurora.a *= Color.a;
			return aurora;
		}
	]]
}

BlendState BlendState
{
	BlendEnable = yes
	SourceBlend = "SRC_ALPHA"
	DestBlend = "INV_SRC_ALPHA"
}

Effect Up
{
	VertexShader = "VertexShader"
	PixelShader = "PixelShaderAurora"
}

Effect Down
{
	VertexShader = "VertexShader"
	PixelShader = "PixelShaderAurora"
}

Effect Over
{
	VertexShader = "VertexShader"
	PixelShader = "PixelShaderAurora"
}

Effect Disable
{
	VertexShader = "VertexShader"
	PixelShader = "PixelShaderAurora"
}