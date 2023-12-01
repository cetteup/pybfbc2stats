# Keys

Available stats keys for Battlefield: Bad Company 2. Extracted from the game files (`startup-00.fbrb`). Verified through additional research and testing.

**Note:**
- All values are received as floating/decimal point numbers. The types listed in the tables refer to types the values could sensibly be casted to/stored as.
- Timestamps are received as the number of days since January 1, 2008 (`2008-01-01T00:00:00+00:00`).

## General

| Key              | Description                                                                                         | Type  |
|------------------|-----------------------------------------------------------------------------------------------------|-------|
| accuracy         | Overall accuracy                                                                                    | float |
| c___h_g          | Heals                                                                                               | int   |
| c___msa_g        | Motion sensor spot assists                                                                          | int   |
| c___r_g          | Repairs                                                                                             | int   |
| c___res_g        | Resupplies                                                                                          | int   |
| c___rev_g        | Revives                                                                                             | int   |
| c___tag_g        | Tracer darts planted                                                                                | int   |
| c__as_ko_g       | Assault kit kills                                                                                   | int   |
| c__de_ko_g       | Engineer kit kills                                                                                  | int   |
| c__re_ko_g       | Recon kit kills                                                                                     | int   |
| c__sp_ko_g       | \[Unused, relict from Bad Company\]                                                                 | int   |
| c__su_ko_g       | Medic kit kills                                                                                     | int   |
| c_as__da_g       | Assault kit deaths                                                                                  | int   |
| c_de__da_g       | Engineer kit deaths                                                                                 | int   |
| c_loss_att_out_g | Games lost as attacker                                                                              | int   |
| c_loss_def_out_g | Games lost as defender                                                                              | int   |
| c_re__da_g       | Recon kit deaths                                                                                    | int   |
| c_sp__da_g       | \[Unused, relict from Bad Company\]                                                                 | int   |
| c_su__da_g       | Medic kit deaths                                                                                    | int   |
| c_win_att_out_g  | Games won as attacker                                                                               | int   |
| c_win_def_out_g  | Games won as defender                                                                               | int   |
| deaths           | Overall deaths                                                                                      | int   |
| demo_rank        | \[Unused, relict from Bad Company\]                                                                 | int   |
| dogr             | Number of dogtags taken from player (non-unique)                                                    | int   |
| dogt             | Number of dogtags taken from (other) players (non-unique)                                           | int   |
| elo              | ?                                                                                                   | float |
| elo0             | ?                                                                                                   | float |
| elo1             | ?                                                                                                   | float |
| form             | ?                                                                                                   | int   |
| games            | Games played                                                                                        | int   |
| goldedition      | \[Unused, relict from Bad Company\]                                                                 | bool  |
| kills            | Overall kills                                                                                       | int   |
| level            | ?                                                                                                   | int   |
| losses           | Games lost                                                                                          | int   |
| rank             | Rank (0-50, [details](https://battlefield.fandom.com/wiki/Battlefield:_Bad_Company_2_online_ranks)) | int   |
| sc_assault       | Assault kit score                                                                                   | int   |
| sc_award         | Award score                                                                                         | int   |
| sc_bonus         | Bonus score                                                                                         | int   |
| sc_demo          | Engineer kit score                                                                                  | int   |
| sc_general       | General score                                                                                       | int   |
| sc_objective     | Objective score                                                                                     | int   |
| sc_recon         | Recon kit score                                                                                     | int   |
| sc_squad         | Squad score                                                                                         | int   |
| sc_support       | Medic kit score                                                                                     | int   |
| sc_team          | Team score                                                                                          | int   |
| sc_vehicle       | Vehicle score                                                                                       | int   |
| score            | Overall score                                                                                       | int   |
| slevel           | ?                                                                                                   | ?     |
| spm              | ?                                                                                                   | ?     |
| spm0             | ?                                                                                                   | ?     |
| spm1             | ?                                                                                                   | ?     |
| srank            | ?                                                                                                   | ?     |
| sveteran         | ?                                                                                                   | ?     |
| teamkills        | Overall teamkills                                                                                   | int   |
| time             | Time played (in seconds)                                                                            | float |
| time_mp002_c     | ?                                                                                                   | ?     |
| time_mp002_h     | ?                                                                                                   | ?     |
| time_mp002_hc    | ?                                                                                                   | ?     |
| time_mp002_n     | ?                                                                                                   | ?     |
| time_mp004_c     | ?                                                                                                   | ?     |
| time_mp004_h     | ?                                                                                                   | ?     |
| time_mp004_hc    | ?                                                                                                   | ?     |
| time_mp004_n     | ?                                                                                                   | ?     |
| time_mp005_c     | ?                                                                                                   | ?     |
| time_mp005_h     | ?                                                                                                   | ?     |
| time_mp005_hc    | ?                                                                                                   | ?     |
| time_mp005_n     | ?                                                                                                   | ?     |
| time_mp008_c     | ?                                                                                                   | ?     |
| time_mp008_h     | ?                                                                                                   | ?     |
| time_mp008_hc    | ?                                                                                                   | ?     |
| time_mp008_n     | ?                                                                                                   | ?     |
| udogt            | Number of dogtags taken from (other) players (unique)                                               | int   |
| ul_40mmsg        | 40mm shotgun gadget unlocked                                                                        | bool  |
| ul_40mmsmk       | 40mm smoke grenade launcher gadget unlocked                                                         | bool  |
| ul_aks74u        | ?                                                                                                   | ?     |
| ul_ammb          | Ammo box gadget unlocked                                                                            | ?     |
| ul_an94          | AN94 assault rifle unlocked                                                                         | ?     |
| ul_atm           | Anti-tank mine gadget unlocked                                                                      | ?     |
| ul_aug           | ?                                                                                                   | ?     |
| ul_aui           | ?                                                                                                   | ?     |
| ul_bay           | ?                                                                                                   | ?     |
| ul_c4timed       | ?                                                                                                   | ?     |
| ul_defi          | Defibrillator gadget unlocked                                                                       | ?     |
| ul_f2000         | F2000 assault rifle unlocked                                                                        | ?     |
| ul_g3            | ?                                                                                                   | ?     |
| ul_gol           | ?                                                                                                   | ?     |
| ul_ld            | ?                                                                                                   | ?     |
| ul_m1            | ?                                                                                                   | ?     |
| ul_m136          | ?                                                                                                   | ?     |
| ul_m16           | ?                                                                                                   | ?     |
| ul_m16k          | ?                                                                                                   | ?     |
| ul_m1911         | ?                                                                                                   | ?     |
| ul_m1a1          | ?                                                                                                   | ?     |
| ul_m249          | ?                                                                                                   | ?     |
| ul_m2cg          | ?                                                                                                   | ?     |
| ul_m416          | ?                                                                                                   | ?     |
| ul_m60           | ?                                                                                                   | ?     |
| ul_m93r          | ?                                                                                                   | ?     |
| ul_m95           | ?                                                                                                   | ?     |
| ul_m95k          | ?                                                                                                   | ?     |
| ul_mcs           | ?                                                                                                   | ?     |
| ul_medk          | ?                                                                                                   | ?     |
| ul_mg3           | ?                                                                                                   | ?     |
| ul_mg36          | ?                                                                                                   | ?     |
| ul_mg3k          | ?                                                                                                   | ?     |
| ul_mk14ebr       | ?                                                                                                   | ?     |
| ul_mots          | ?                                                                                                   | ?     |
| ul_mp412         | ?                                                                                                   | ?     |
| ul_mp443         | ?                                                                                                   | ?     |
| ul_mst           | ?                                                                                                   | ?     |
| ul_n2k           | ?                                                                                                   | ?     |
| ul_pp2           | ?                                                                                                   | ?     |
| ul_qbu88         | ?                                                                                                   | ?     |
| ul_qby88         | ?                                                                                                   | ?     |
| ul_qju88         | ?                                                                                                   | ?     |
| ul_rept          | ?                                                                                                   | ?     |
| ul_s12k          | ?                                                                                                   | ?     |
| ul_scar          | ?                                                                                                   | ?     |
| ul_sp_alt_a      | ?                                                                                                   | ?     |
| ul_sp_alt_r      | ?                                                                                                   | ?     |
| ul_sp_alt_s      | ?                                                                                                   | ?     |
| ul_sp_ammsupp    | ?                                                                                                   | ?     |
| ul_sp_assault_a  | ?                                                                                                   | ?     |
| ul_sp_assault_r  | ?                                                                                                   | ?     |
| ul_sp_assault_s  | ?                                                                                                   | ?     |
| ul_sp_bodarm     | ?                                                                                                   | ?     |
| ul_sp_buldmplus  | ?                                                                                                   | ?     |
| ul_sp_coaxmg     | ?                                                                                                   | ?     |
| ul_sp_expdmplus  | ?                                                                                                   | ?     |
| ul_sp_expsupp    | ?                                                                                                   | ?     |
| ul_sp_grsupp     | ?                                                                                                   | ?     |
| ul_sp_harveharm  | ?                                                                                                   | ?     |
| ul_sp_lmg_aim    | ?                                                                                                   | ?     |
| ul_sp_lmg_r      | ?                                                                                                   | ?     |
| ul_sp_lmg_s      | ?                                                                                                   | ?     |
| ul_sp_medheal    | ?                                                                                                   | ?     |
| ul_sp_medradius  | ?                                                                                                   | ?     |
| ul_sp_sczmplus   | ?                                                                                                   | ?     |
| ul_sp_shotgun_c  | ?                                                                                                   | ?     |
| ul_sp_shotgun_f  | ?                                                                                                   | ?     |
| ul_sp_shotgun_s  | ?                                                                                                   | ?     |
| ul_sp_smg_a      | ?                                                                                                   | ?     |
| ul_sp_smg_r      | ?                                                                                                   | ?     |
| ul_sp_smg_s      | ?                                                                                                   | ?     |
| ul_sp_sniper_r   | ?                                                                                                   | ?     |
| ul_sp_sniper_s   | ?                                                                                                   | ?     |
| ul_sp_sprint     | ?                                                                                                   | ?     |
| ul_sp_spscope    | ?                                                                                                   | ?     |
| ul_sp_tnsmk      | ?                                                                                                   | ?     |
| ul_sp_tnzm       | ?                                                                                                   | ?     |
| ul_sp_vdamage    | ?                                                                                                   | ?     |
| ul_sp_vehmosens  | ?                                                                                                   | ?     |
| ul_sp_vreload    | ?                                                                                                   | ?     |
| ul_spas12        | ?                                                                                                   | ?     |
| ul_spas15        | ?                                                                                                   | ?     |
| ul_sv98          | ?                                                                                                   | ?     |
| ul_svu           | ?                                                                                                   | ?     |
| ul_t194          | ?                                                                                                   | ?     |
| ul_trad          | ?                                                                                                   | ?     |
| ul_u12           | ?                                                                                                   | ?     |
| ul_ump           | ?                                                                                                   | ?     |
| ul_umpk          | ?                                                                                                   | ?     |
| ul_uzi           | ?                                                                                                   | ?     |
| ul_vss           | ?                                                                                                   | ?     |
| ul_xm8           | ?                                                                                                   | ?     |
| ul_xm8c          | ?                                                                                                   | ?     |
| ul_xm8lmg        | ?                                                                                                   | ?     |
| veteran          | ?                                                                                                   | ?     |
| webstats         | ?                                                                                                   | ?     |
| webvet           | ?                                                                                                   | ?     |
| wins             | ?                                                                                                   | ?     |

## Weapons

**Images:** http://bfbc2.statsverse.com/images/stats/weapons_128x32/{weapon}.png ([Example](http://bfbc2.statsverse.com/images/stats/weapons_128x32/9a91.png))

### Pattern

| Attribute           | Measuring (as per game files)   | Description (from game files) |
|---------------------|---------------------------------|-------------------------------|

### Keys

| Key                  | Description                                    | Type  |
|----------------------|------------------------------------------------|-------|

## Vehicles

**Images:** http://bfbc2.statsverse.com/images/stats/vehicles_128x32/{weapon}.png ([Example](http://bfbc2.statsverse.com/images/stats/vehicles_128x32/ah60.png))

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

[//]: # ( TODO: Check if this is the case for BC2 as well, update example keys )
¹ stop counting once the award was obtained (e.g. c_ac11___ccp_g stops at 5, c_ac12___ccp_g at 25 control points captured)

### Achievements

Achievements can only be awarded once, so the `{award}_00` values (number of times awarded) will all be `0.0` or `1.0`.

**Images:** http://bfbc2.statsverse.com/images/stats/achievements_96x96/{base-key}.png ([Example](http://bfbc2.statsverse.com/images/stats/achievements_96x96/31.png))

| Key                    | Description                                                                           | Type  |
|------------------------|---------------------------------------------------------------------------------------|-------|

### Wildcards

Wildcards can only be awarded once, so the `{award}_00` values (number of times awarded) will all be `0.0` or `1.0`.

**Images:** http://bfbc2.statsverse.com/images/stats/wildcards_96x96/{base-key}.png ([Example](http://bfbc2.statsverse.com/images/stats/wildcards_96x96/wc01.png))

| Key                    | Description                                                                                                 | Type  |
|------------------------|-------------------------------------------------------------------------------------------------------------|-------|

### Patches

Patches can only be awarded once, so the `{award}_00` values (number of times awarded) will all be `0.0` or `1.0`.

**Images:** http://bfbc2.statsverse.com/images/stats/patches_96x96/{base-key}.png ([Example](http://bfbc2.statsverse.com/images/stats/patches_96x96/pb01.png))

| Key                    | Description                                                                                                 | Type  |
|------------------------|-------------------------------------------------------------------------------------------------------------|-------|

### Trophies

Trophies can be awarded any number of times, so the `{award}_00` values (number of times awarded) can be `0.0` or any positive number. Requirements must be fulfilled within a single round, which why stamps do not have keys indicating progress. 

**Images:** http://bfbc2.statsverse.com/images/stats/trophies_96x96/{base-key}.png ([Example](http://bfbc2.statsverse.com/images/stats/trophies_96x96/t01.png))

| Key      | Description                                                                                        | Type  |
|----------|----------------------------------------------------------------------------------------------------|-------|
