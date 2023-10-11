# Keys

Available stats keys for Battlefield: Bad Company. Extracted from the game files (`startup-00.fbrb`). Verified through additional research and testing.

**Note:**
- All values are received as floating/decimal point numbers. The types listed in the tables refer to types the values could sensibly be casted to/stored as.
- Timestamps are received as the number of days since January 1, 2008 (`2008-01-01T00:00:00+00:00`).

## General

Unlock status for the following weapons is not tracked as distinct keys, as they are included in the gold edition or unlocked by reaching rank 25:
* AN94 assault rifle
* SPAS15 shotgun
* VSS scoped rifle
* XM8C submachine gun
* MG3 light machine gun

| Key              | Description                                                                                           | Type  |
|------------------|-------------------------------------------------------------------------------------------------------|-------|
| accuracy         | Overall accuracy                                                                                      | float |
| c__as_ko_g       | Assault kit kills                                                                                     | int   |
| c__de_ko_g       | Demolition kit kills                                                                                  | int   |
| c__re_ko_g       | Recon kit kills                                                                                       | int   |
| c__sp_ko_g       | Specialist kit kills                                                                                  | int   |
| c__su_ko_g       | Support kit kills                                                                                     | int   |
| c_as__da_g       | Assault kit deaths                                                                                    | int   |
| c_de__da_g       | Demolition kit deaths                                                                                 | int   |
| c_loss_att_out_g | Games lost as attacker                                                                                | int   |
| c_loss_def_out_g | Games lost as defender                                                                                | int   |
| c_re__da_g       | Recon kit deaths                                                                                      | int   |
| c_sp__da_g       | Specialist kit deaths                                                                                 | int   |
| c_su__da_g       | Support kit deaths                                                                                    | int   |
| c_win_att_out_g  | Games won as attacker                                                                                 | int   |
| c_win_def_out_g  | Games won as defender                                                                                 | int   |
| deaths           | Overall deaths                                                                                        | int   |
| demo_rank        | Rank reached in demo version                                                                          | int   |
| dogr             | Number of dogtags taken from player (non-unique)                                                      | int   |
| dogt             | Number of dogtags taken from (other) players (non-unique)                                             | int   |
| elo              | ?                                                                                                     | float |
| elo0             | ?                                                                                                     | float |
| elo1             | ?                                                                                                     | float |
| form             | ?                                                                                                     | int   |
| games            | Games played                                                                                          | int   |
| goldedition      | Player owns gold edition                                                                              | bool  |
| kills            | Overall kills                                                                                         | ?     |
| le_an94          | ?                                                                                                     | ?     |
| le_mg3           | ?                                                                                                     | ?     |
| le_spas15        | ?                                                                                                     | ?     |
| le_vss           | ?                                                                                                     | ?     |
| le_xm8c          | ?                                                                                                     | ?     |
| level            | ?                                                                                                     | int   |
| losses           | Games lost                                                                                            | int   |
| mp_an94          | ?                                                                                                     | ?     |
| mp_atm           | ?                                                                                                     | ?     |
| mp_aui           | ?                                                                                                     | ?     |
| mp_c4            | ?                                                                                                     | ?     |
| mp_f2000         | ?                                                                                                     | ?     |
| mp_ld            | ?                                                                                                     | ?     |
| mp_m16           | ?                                                                                                     | ?     |
| mp_m60           | ?                                                                                                     | ?     |
| mp_m95           | ?                                                                                                     | ?     |
| mp_mg3           | ?                                                                                                     | ?     |
| mp_mg36          | ?                                                                                                     | ?     |
| mp_mrt           | ?                                                                                                     | ?     |
| mp_ns2000        | ?                                                                                                     | ?     |
| mp_pp2000        | ?                                                                                                     | ?     |
| mp_qby88         | ?                                                                                                     | ?     |
| mp_spas12        | ?                                                                                                     | ?     |
| mp_spas15        | ?                                                                                                     | ?     |
| mp_svu           | ?                                                                                                     | ?     |
| mp_ump           | ?                                                                                                     | ?     |
| mp_usas12        | ?                                                                                                     | ?     |
| mp_uzi           | ?                                                                                                     | ?     |
| mp_vss           | ?                                                                                                     | ?     |
| mp_xm8           | ?                                                                                                     | ?     |
| mp_xm8c          | ?                                                                                                     | ?     |
| mp_xm8lmg        | ?                                                                                                     | ?     |
| rank             | Rank (0-25, [details](https://battlefield.fandom.com/wiki/Battlefield:_Bad_Company_Online_Ranks))     | int   |
| re_f2000         | F2000 assault rifle unlocked ([trivia](https://battlefield.fandom.com/wiki/F2000/Bad_Company#Trivia)) | bool  |
| re_m60           | M60 light machine gun unlocked                                                                        | bool  |
| re_qby88         | QBU88 scoped rifle unlocked                                                                           | bool  |
| re_usas12        | USAS12 shotgun unlocked                                                                               | bool  |
| re_uzi           | UZI submachine gun unlocked                                                                           | bool  |
| sc_bonus         | Bonus score                                                                                           | ?     |
| sc_general       | General score                                                                                         | ?     |
| sc_objective     | Objective score                                                                                       | ?     |
| sc_squad         | Squad score                                                                                           | ?     |
| sc_team          | Team score                                                                                            | ?     |
| score            | Overall score                                                                                         | ?     |
| slevel           | ?                                                                                                     | ?     |
| spm              | ?                                                                                                     | float |
| spm0             | ?                                                                                                     | float |
| spm1             | ?                                                                                                     | float |
| srank            | ? "Seen rank" (difference between srank and rank seems to trigger rank up shown in game)              | int   |
| sveteran         | ?                                                                                                     | int   |
| teamkills        | Overall teamkills                                                                                     | int   |
| time             | Time played (in seconds)                                                                              | float |
| ts_atm           | ?                                                                                                     | ?     |
| ts_aui           | ?                                                                                                     | ?     |
| ts_c4            | ?                                                                                                     | ?     |
| ts_ld            | ?                                                                                                     | ?     |
| ts_m16           | ?                                                                                                     | ?     |
| ts_m95           | ?                                                                                                     | ?     |
| ts_mg36          | ?                                                                                                     | ?     |
| ts_mrt           | ?                                                                                                     | ?     |
| ts_ns2000        | ?                                                                                                     | ?     |
| ts_pp2000        | ?                                                                                                     | ?     |
| ts_spas12        | ?                                                                                                     | ?     |
| ts_svu           | ?                                                                                                     | ?     |
| ts_ump           | ?                                                                                                     | ?     |
| ts_xm8           | ?                                                                                                     | ?     |
| ts_xm8lmg        | ?                                                                                                     | ?     |
| udogt            | Number of dogtags taken from (other) players (unique)                                                 | int   |
| ul_atm           | ATM-00 vehicle mine unlocked                                                                          | bool  |
| ul_aui           | LIFE-2 chemical dispenser unlocked                                                                    | bool  |
| ul_c4            | ? DTN-4 explosives unlocked                                                                           | bool  |
| ul_ld            | LZ-537 target designator unlocked                                                                     | bool  |
| ul_m16           | M16 assault rifle unlocked                                                                            | bool  |
| ul_m95           | M95 scoped rifle unlocked                                                                             | bool  |
| ul_mg36          | MG36 light machine gun unlocked                                                                       | bool  |
| ul_mrt           | MRTR-5 mortar unlocked                                                                                | bool  |
| ul_ns2000        | NS2000 shotgun unlocked                                                                               | bool  |
| ul_pp2000        | PP2000 submarine gun unlocked                                                                         | bool  |
| ul_spas12        | SPAS12 shotgun unlocked                                                                               | bool  |
| ul_svu           | SVU scoped rifle unlocked                                                                             | bool  |
| ul_ump           | UMP submachine gun unlocked                                                                           | bool  |
| ul_xm8           | XM8 assault rifle unlocked                                                                            | bool  |
| ul_xm8lmg        | XM8 light machine gun unlocked                                                                        | bool  |
| veteran          | Veteran status/rank ([info](https://battlefield.fandom.com/wiki/Battlefield_Veteran))                 | int   |
| webstats         | ?                                                                                                     | ?     |
| webvet           | ?                                                                                                     | int   |
| wins             | Games won                                                                                             | ?     |

## Weapons

**Images:** http://bfbc.statsverse.com/images/stats/weapons_128x32/{weapon}.png ([Example](http://bfbc.statsverse.com/images/stats/weapons_128x32/9a91.png))

### Pattern

| Attribute           | Measuring (as per game files)   | Description (from game files) |
|---------------------|---------------------------------|-------------------------------|

### Keys

| Key                  | Description                                    | Type  |
|----------------------|------------------------------------------------|-------|

## Vehicles

**Images:** http://bfbc.statsverse.com/images/stats/vehicles_128x32/{weapon}.png ([Example](http://bfbc.statsverse.com/images/stats/vehicles_128x32/ah60.png))

### Pattern

| Attribute               | Measuring (as per game files) | Description (from game files) |
|-------------------------|-------------------------------|-------------------------------|

### Keys

| Key                   | Description                                       | Type  |
|-----------------------|---------------------------------------------------|-------|

## Awards

### Pattern

There are at least two keys per awards, always following the same pattern.

| Attribute       | Description                                                                 |
|-----------------|-----------------------------------------------------------------------------|
| `{award}_00`    | Number of times awarded                                                     |
| `{award}_01`    | Timestamp when (last) awarded                                               |
| `c_{award}_...` | Key indicating progress towards award (optional, award may have multiple) ¹ |

[//]: # ( TODO: Check if this is the case for BC as well, update example keys )
¹ stop counting once the award was obtained (e.g. c_ac11___ccp_g stops at 5, c_ac12___ccp_g at 25 control points captured)

### Achievements

Achievements can only be awarded once, so the `{award}_00` values (number of times awarded) will all be `0.0` or `1.0`.

**Images:** http://bfbc.statsverse.com/images/stats/achievements_96x96/{base-key}.png ([Example](http://bfbc.statsverse.com/images/stats/achievements_96x96/ac33.png))

| Key                    | Description                                                                           | Type  |
|------------------------|---------------------------------------------------------------------------------------|-------|

### Wildcards

Wildcards can only be awarded once, so the `{award}_00` values (number of times awarded) will all be `0.0` or `1.0`.

**Images:** http://bfbc.statsverse.com/images/stats/wildcards_96x96/{base-key}.png ([Example](http://bfbc.statsverse.com/images/stats/wildcards_96x96/wc01.png))

| Key                    | Description                                                                                                 | Type  |
|------------------------|-------------------------------------------------------------------------------------------------------------|-------|

### Patches

Patches can only be awarded once, so the `{award}_00` values (number of times awarded) will all be `0.0` or `1.0`.

**Images:** http://bfbc.statsverse.com/images/stats/patches_96x96/{base-key}.png ([Example](http://bfbc.statsverse.com/images/stats/patches_96x96/pb01.png))

| Key                    | Description                                                                                                 | Type  |
|------------------------|-------------------------------------------------------------------------------------------------------------|-------|

### Trophies

Trophies can be awarded any number of times, so the `{award}_00` values (number of times awarded) can be `0.0` or any positive number. Requirements must be fulfilled within a single round, which why stamps do not have keys indicating progress. 

**Images:** http://bfbc.statsverse.com/images/stats/trophies_96x96/{base-key}.png ([Example](http://bfbc.statsverse.com/images/stats/trophies_96x96/t01.png))

| Key      | Description                                                                                        | Type  |
|----------|----------------------------------------------------------------------------------------------------|-------|
