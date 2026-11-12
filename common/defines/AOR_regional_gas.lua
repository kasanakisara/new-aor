-- Original nukes technology (.5) and original reactor factor (+300%).
-- First facility: .5 * (1 + 3) / 200 = .01 units/day.
NDefines.NRaids.NUCLEAR_BOMB_PRODUCTION_SCALE = 200.0

-- Native risk settings are shared by all raid types. Avoid the 25% disaster cap on high-risk success.
NDefines.NRaids.RAID_LOW_RISK_SETTING_SUCCESS_MODIFIER = 0.0
NDefines.NRaids.RAID_MEDIUM_RISK_SETTING_SUCCESS_MODIFIER = 0.10
NDefines.NRaids.RAID_HIGH_RISK_SETTING_SUCCESS_MODIFIER = 0.25
NDefines.NRaids.RAID_LOW_RISK_SETTING_DISASTER_MODIFIER = 0.0
NDefines.NRaids.RAID_MEDIUM_RISK_SETTING_DISASTER_MODIFIER = 0.05
NDefines.NRaids.RAID_HIGH_RISK_SETTING_DISASTER_MODIFIER = 0.10
