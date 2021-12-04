from enum import Enum


class Step(int, Enum):
    pass


class FeslStep(Step):
    hello = 1
    login = 2


class TheaterStep(Step):
    conn = 1
    user = 2


class Namespace(bytes, Enum):
    pc = b'battlefield'
    xbox360 = b'xbox'
    ps3 = b'ps3'
    cem_ea_id = b'cem_ea_id'


class LookupType(bytes, Enum):
    byName = b'userName'
    byId = b'userId'


class Platform(int, Enum):
    pc = 1
    # XBOX is not yet supported
    # xbox360 = 2
    ps3 = 3


DEFAULT_BUFFER_SIZE = 8096
HEADER_LENGTH = 12
VALID_HEADER_TYPES = [b'acct', b'fsys', b'rank',
                      b'CONN', b'USER', b'LLST', b'LDAT', b'GLST', b'GDAT', b'GDET', b'PDAT', b'PING']
HEADER_ONLY_PACKET_HEADERS = [b'PING\x00\x00\x00\x00\x00\x00\x00\x0c']
BACKEND_DETAILS = {
    Platform.pc: {
        'host': 'bfbc2-pc-server.fesl.ea.com',
        'port': 18321,
        'clientString': b'bfbc2-pc'
    },
    Platform.ps3: {
        'host': 'bfbc2-ps3-server.fesl.ea.com',
        'port': 18331,
        'clientString': b'bfbc2-ps3'
    }
}
DEFAULT_LEADERBOARD_KEYS = [b'deaths', b'kills', b'score', b'time']
STATS_KEYS = [b'accuracy', b'br40mmgl_00', b'br40mmgl_01', b'br40mmsg_00', b'br40mmsg_01', b'br9a91_00', b'br9a91_01',
              b'braek_00', b'braek_01', b'brair_00', b'brair_01', b'brak47v_00', b'brak47v_01', b'braks74u_00',
              b'braks74u_01', b'bran94_00', b'bran94_01', b'brarm_00', b'brarm_01', b'bratm_00', b'bratm_01',
              b'braug_00', b'braug_01', b'brc4_00', b'brc4_01', b'brf2000_00', b'brf2000_01', b'brg3_00', b'brg3_01',
              b'brgol_00', b'brgol_01', b'brhgr_00', b'brhgr_01', b'brm136_00', b'brm136_01', b'brm16_00', b'brm16_01',
              b'brm16a1v_00', b'brm16a1v_01', b'brm16k_00', b'brm16k_01', b'brm1911_00', b'brm1911_01', b'brm1_00',
              b'brm1_01', b'brm1a1_00', b'brm1a1_01', b'brm21v_00', b'brm21v_01', b'brm249_00', b'brm249_01',
              b'brm24_00', b'brm24_01', b'brm2cg_00', b'brm2cg_01', b'brm2v_00', b'brm2v_01', b'brm40v_00',
              b'brm40v_01', b'brm416_00', b'brm416_01', b'brm60_00', b'brm60_01', b'brm60v_00', b'brm60v_01',
              b'brm93r_00', b'brm93r_01', b'brm95_00', b'brm95_01', b'brm95k_00', b'brm95k_01', b'brm9_00', b'brm9_01',
              b'brmac10v_00', b'brmac10v_01', b'brmcs_00', b'brmcs_01', b'brmel_00', b'brmel_01', b'brmg36_00',
              b'brmg36_01', b'brmg3_00', b'brmg3_01', b'brmg3k_00', b'brmg3k_01', b'brmk14ebr_00', b'brmk14ebr_01',
              b'brmp412_00', b'brmp412_01', b'brmst_00', b'brmst_01', b'brn2k_00', b'brn2k_01', b'brpkm_00',
              b'brpkm_01', b'brpp2_00', b'brpp2_01', b'brppshv_00', b'brppshv_01', b'brqbu88_00', b'brqbu88_01',
              b'brqju88_00', b'brqju88_01', b'brrpg7_00', b'brrpg7_01', b'brrpkv_00', b'brrpkv_01', b'brs12k_00',
              b'brs12k_01', b'brscar_00', b'brscar_01', b'brsea_00', b'brsea_01', b'brspas12_00', b'brspas12_01',
              b'brstav_00', b'brstav_01', b'brsv98_00', b'brsv98_01', b'brsvdv_00', b'brsvdv_01', b'brsvu_00',
              b'brsvu_01', b'brtt33v_00', b'brtt33v_01', b'brtveh_00', b'brtveh_01', b'bru12_00', b'bru12_01',
              b'brump_00', b'brump_01', b'brumpk_00', b'brumpk_01', b'bruzi_00', b'bruzi_01', b'brvss_00', b'brvss_01',
              b'brxm22v_00', b'brxm22v_01', b'brxm8_00', b'brxm8_01', b'brxm8c_00', b'brxm8c_01', b'brxm8lmg_00',
              b'brxm8lmg_01', b'c_40mmgl__kw_g', b'c_40mmgl__sfw_g', b'c_40mmgl__shw_g', b'c_40mmgl__sw_g',
              b'c_40mmsg__kw_g', b'c_40mmsg__sfw_g', b'c_40mmsg__shw_g', b'c_40mmsg__sw_g', b'c_9a91__kw_g',
              b'c_9a91__sfw_g', b'c_9a91__shw_g', b'c_9a91__sw_g', b'c_KORD__si_g', b'c_KORN__si_g', b'c_MI28__ddw_g',
              b'c_MI28__si_g', b'c_PBLB__ddw_g', b'c_PBLB__si_g', b'c_QLZ8__si_g', b'c_TOW2__si_g', b'c_VADS__si_g',
              b'c_XM307__si_g', b'c_XM312__si_g', b'c__40mmgl_hsh_g', b'c__40mmsg_hsh_g', b'c__9a91_hsh_g',
              b'c__KORD_ki_g', b'c__KORN_ki_g', b'c__MI28_ki_g', b'c__PBLB_ki_g', b'c__QLZ8_ki_g', b'c__TOW2_ki_g',
              b'c__VADS_ki_g', b'c__XM307_ki_g', b'c__XM312_ki_g', b'c___h_g', b'c___msa_g', b'c___r_g', b'c___res_g',
              b'c___rev_g', b'c___tag_g', b'c__aav_ki_g', b'c__aaw_hsh_g', b'c__aek_hsh_g', b'c__ah60_ki_g',
              b'c__ah64_ki_g', b'c__ak47v_hsh_g', b'c__aks74u_hsh_g', b'c__an94_hsh_g', b'c__as_ko_g', b'c__aug_hsh_g',
              b'c__bmd3_ki_g', b'c__bmda_ki_g', b'c__boaw_hsh_g', b'c__cav_ki_g', b'c__cobr_ki_g', b'c__de_ko_g',
              b'c__defi_hsh_g', b'c__f2000_hsh_g', b'c__g3_hsh_g', b'c__gaz69v_ki_g', b'c__gol_hsh_g', b'c__havoc_ki_g',
              b'c__helw_hsh_g', b'c__hmv_ki_g', b'c__hueyv_ki_g', b'c__jets_ki_g', b'c__m15v_ki_g', b'c__m16_hsh_g',
              b'c__m16a1v_hsh_g', b'c__m16k_hsh_g', b'c__m1911_hsh_g', b'c__m1_hsh_g', b'c__m1a1_hsh_g',
              b'c__m1a2_ki_g', b'c__m21v_hsh_g', b'c__m249_hsh_g', b'c__m24_hsh_g', b'c__m2v_hsh_g', b'c__m3a3_ki_g',
              b'c__m40v_hsh_g', b'c__m416_hsh_g', b'c__m48v_ki_g', b'c__m60_hsh_g', b'c__m60v_hsh_g', b'c__m93r_hsh_g',
              b'c__m95_hsh_g', b'c__m95k_hsh_g', b'c__m9_hsh_g', b'c__mac10v_hsh_g', b'c__mcs_hsh_g', b'c__mg36_hsh_g',
              b'c__mg3_hsh_g', b'c__mg3k_hsh_g', b'c__mk14ebr_hsh_g', b'c__mp412_hsh_g', b'c__n2k_hsh_g',
              b'c__pbrv_ki_g', b'c__pkm_hsh_g', b'c__pp2_hsh_g', b'c__ppshv_hsh_g', b'c__prtg_hsh_g', b'c__qbu88_hsh_g',
              b'c__qju88_hsh_g', b'c__quad_ki_g', b'c__re_ko_g', b'c__rept_hsh_g', b'c__rpkv_hsh_g', b'c__s12k_hsh_g',
              b'c__scar_hsh_g', b'c__smol_hsh_g', b'c__spas12_hsh_g', b'c__stgl_hsh_g', b'c__stmg_hsh_g', b'c__su_ko_g',
              b'c__sv98_hsh_g', b'c__svdv_hsh_g', b'c__svu_hsh_g', b'c__t54v_ki_g', b'c__t90_ki_g', b'c__tanc_hsh_g',
              b'c__tanm_hsh_g', b'c__tt33v_hsh_g', b'c__u12_hsh_g', b'c__uav_ki_g', b'c__ump_hsh_g', b'c__umpk_hsh_g',
              b'c__uzi_hsh_g', b'c__vodn_ki_g', b'c__vss_hsh_g', b'c__xm22v_hsh_g', b'c__xm8_hsh_g', b'c__xm8c_hsh_g',
              b'c__xm8lmg_hsh_g', b'c_aav__si_g', b'c_aaw__kw_g', b'c_aek__kw_g', b'c_aek__sfw_g', b'c_aek__shw_g',
              b'c_aek__sw_g', b'c_ah60__ddw_g', b'c_ah60__si_g', b'c_ah64__ddw_g', b'c_ah64__si_g', b'c_ak47v__kw_g',
              b'c_ak47v__sfw_g', b'c_ak47v__shw_g', b'c_ak47v__sw_g', b'c_aks74u__kw_g', b'c_aks74u__sfw_g',
              b'c_aks74u__shw_g', b'c_aks74u__sw_g', b'c_ammb__kw_g', b'c_ammb__sfw_g', b'c_ammb__shw_g',
              b'c_ammb__sw_g', b'c_an94__kw_g', b'c_an94__sfw_g', b'c_an94__shw_g', b'c_an94__sw_g', b'c_as__da_g',
              b'c_atm__kw_g', b'c_atm__sfw_g', b'c_atm__shw_g', b'c_atm__sw_g', b'c_aug__kw_g', b'c_aug__sfw_g',
              b'c_aug__shw_g', b'c_aug__sw_g', b'c_bmd3__ddw_g', b'c_bmd3__si_g', b'c_bmda__ddw_g', b'c_bmda__si_g',
              b'c_boaw__kw_g', b'c_br40mmgl_40mmgl__kw_g', b'c_br40mmsg_40mmsg__kw_g', b'c_br9a91_9a91__kw_g',
              b'c_braek_aek__kw_g', b'c_brair__air_ki_g', b'c_brak47v_ak47v__kw_g', b'c_braks74u_aks74u__kw_g',
              b'c_bran94_an94__kw_g', b'c_brarm__arm_ki_g', b'c_bratm_atm__kw_g', b'c_braug_aug__kw_g',
              b'c_brc4_c4__kw_g', b'c_brf2000_f2000__kw_g', b'c_brg3_g3__kw_g', b'c_brgol_gol__kw_g',
              b'c_brhgr_hgr__kw_g', b'c_brm136_m136__kw_g', b'c_brm16_m16__kw_g', b'c_brm16a1v_m16a1v__kw_g',
              b'c_brm16k_m16k__kw_g', b'c_brm1911_m1911__kw_g', b'c_brm1_m1__kw_g', b'c_brm1a1_m1a1__kw_g',
              b'c_brm21v_m21v__kw_g', b'c_brm249_m249__kw_g', b'c_brm24_m24__kw_g', b'c_brm2cg_m2cg__kw_g',
              b'c_brm2v_m2v__kw_g', b'c_brm40v_m40v__kw_g', b'c_brm416_m416__kw_g', b'c_brm60_m60__kw_g',
              b'c_brm60v_m60v__kw_g', b'c_brm93r_m93r__kw_g', b'c_brm95_m95__kw_g', b'c_brm95k_m95k__kw_g',
              b'c_brm9_m9__kw_g', b'c_brmac10v_mac10v__kw_g', b'c_brmcs_mcs__kw_g', b'c_brmel_mel__kw_g',
              b'c_brmg36_mg36__kw_g', b'c_brmg3_mg3__kw_g', b'c_brmg3k_mg3k__kw_g', b'c_brmk14ebr_mk14ebr__kw_g',
              b'c_brmp412_mp412__kw_g', b'c_brmst_mst__kw_g', b'c_brn2k_n2k__kw_g', b'c_brpkm_pkm__kw_g',
              b'c_brpp2_pp2__kw_g', b'c_brppshv_ppshv__kw_g', b'c_brqbu88_qbu88__kw_g', b'c_brqju88_qju88__kw_g',
              b'c_brrpg7_rpg7__kw_g', b'c_brrpkv_rpkv__kw_g', b'c_brs12k_s12k__kw_g', b'c_brscar_scar__kw_g',
              b'c_brsea__sea_ki_g', b'c_brspas12_spas12__kw_g', b'c_brstav__stav_ki_g', b'c_brsv98_sv98__kw_g',
              b'c_brsvdv_svdv__kw_g', b'c_brsvu_svu__kw_g', b'c_brtt33v_tt33v__kw_g', b'c_brtveh__tveh_ki_g',
              b'c_bru12_u12__kw_g', b'c_brump_ump__kw_g', b'c_brumpk_umpk__kw_g', b'c_bruzi_uzi__kw_g',
              b'c_brvss_vss__kw_g', b'c_brxm22v_xm22v__kw_g', b'c_brxm8_xm8__kw_g', b'c_brxm8c_xm8c__kw_g',
              b'c_brxm8lmg_xm8lmg__kw_g', b'c_c4__kw_g', b'c_c4__sfw_g', b'c_c4__shw_g', b'c_c4__sw_g', b'c_cav__ddw_g',
              b'c_cav__si_g', b'c_cobr__ddw_g', b'c_cobr__si_g', b'c_de__da_g', b'c_defi__kw_g', b'c_defi__sfw_g',
              b'c_defi__shw_g', b'c_defi__sw_g', b'c_deml__kw_g', b'c_f2000__kw_g', b'c_f2000__sfw_g',
              b'c_f2000__shw_g', b'c_f2000__sw_g', b'c_g3__kw_g', b'c_g3__sfw_g', b'c_g3__shw_g', b'c_g3__sw_g',
              b'c_gol__kw_g', b'c_gol__sfw_g', b'c_gol__shw_g', b'c_gol__sw_g', b'c_gaz69v__ddw_g', b'c_gaz69v__si_g',
              b'c_go40mmgl_40mmgl__kw_g', b'c_go40mmsg_40mmsg__kw_g', b'c_go9a91_9a91__kw_g', b'c_goaek_aek__kw_g',
              b'c_goair__air_ki_g', b'c_goak47v_ak47v__kw_g', b'c_goaks74u_aks74u__kw_g', b'c_goan94_an94__kw_g',
              b'c_goarm__arm_ki_g', b'c_goatm_atm__kw_g', b'c_goaug_aug__kw_g', b'c_goc4_c4__kw_g',
              b'c_gof2000_f2000__kw_g', b'c_gog3_g3__kw_g', b'c_gogol_gol__kw_g', b'c_gohgr_hgr__kw_g', b'c_gol__kw_g',
              b'c_gol__sfw_g', b'c_gol__shw_g', b'c_gol__sw_g', b'c_gom136_m136__kw_g', b'c_gom16_m16__kw_g',
              b'c_gom16a1v_m16a1v__kw_g', b'c_gom16k_m16k__kw_g', b'c_gom1911_m1911__kw_g', b'c_gom1_m1__kw_g',
              b'c_gom1a1_m1a1__kw_g', b'c_gom21v_m21v__kw_g', b'c_gom249_m249__kw_g', b'c_gom24_m24__kw_g',
              b'c_gom2cg_m2cg__kw_g', b'c_gom2v_m2v__kw_g', b'c_gom40v_m40v__kw_g', b'c_gom416_m416__kw_g',
              b'c_gom60_m60__kw_g', b'c_gom60v_m60v__kw_g', b'c_gom93r_m93r__kw_g', b'c_gom95_m95__kw_g',
              b'c_gom95k_m95k__kw_g', b'c_gom9_m9__kw_g', b'c_gomac10v_mac10v__kw_g', b'c_gomcs_mcs__kw_g',
              b'c_gomel_mel__kw_g', b'c_gomg36_mg36__kw_g', b'c_gomg3_mg3__kw_g', b'c_gomg3k_mg3k__kw_g',
              b'c_gomk14ebr_mk14ebr__kw_g', b'c_gomp412_mp412__kw_g', b'c_gomst_mst__kw_g', b'c_gon2k_n2k__kw_g',
              b'c_gopkm_pkm__kw_g', b'c_gopp2_pp2__kw_g', b'c_goppshv_ppshv__kw_g', b'c_goqbu88_qbu88__kw_g',
              b'c_goqju88_qju88__kw_g', b'c_gorpg7_rpg7__kw_g', b'c_gorpkv_rpkv__kw_g', b'c_gos12k_s12k__kw_g',
              b'c_goscar_scar__kw_g', b'c_gosea__sea_ki_g', b'c_gospas12_spas12__kw_g', b'c_gostav__stav_ki_g',
              b'c_gosv98_sv98__kw_g', b'c_gosvdv_svdv__kw_g', b'c_gosvu_svu__kw_g', b'c_gott33v_tt33v__kw_g',
              b'c_gotveh__tveh_ki_g', b'c_gou12_u12__kw_g', b'c_goump_ump__kw_g', b'c_goumpk_umpk__kw_g',
              b'c_gouzi_uzi__kw_g', b'c_govss_vss__kw_g', b'c_goxm22v_xm22v__kw_g', b'c_goxm8_xm8__kw_g',
              b'c_goxm8c_xm8c__kw_g', b'c_goxm8lmg_xm8lmg__kw_g', b'c_havoc__ddw_g', b'c_havoc__si_g', b'c_helw__kw_g',
              b'c_hgr__kw_g', b'c_hgr__sfw_g', b'c_hgr__shw_g', b'c_hgr__sw_g', b'c_hmv__ddw_g', b'c_hmv__si_g',
              b'c_hueyv__ddw_g', b'c_hueyv__si_g', b'c_i01___hsh_g', b'c_i02_hg__kw_g', b'c_i03_hgr__kw_g',
              b'c_i04_mel__kw_g', b'c_i05_mel__kw_g', b'c_i06___d_g', b'c_i07_ass__kw_g', b'c_i08_sup__kw_g',
              b'c_i09___vd_g', b'c_i10___tag_g', b'c_i11___kn_g', b'c_i11___nik_g', b'c_i12_re_rec_lrh_g',
              b'c_i13_c4__kw_g', b'c_i14_rec__kw_g', b'c_i15_dem__kw_g', b'c_i16___h_g', b'c_i17___res_g',
              b'c_i18___msa_g', b'c_i19___r_g', b'c_i20___ko_g', b'c_i23_spe__kw_g', b'c_i24_atm__kw_g',
              b'c_i25___dok_g', b'c_i26___hsh_g', b'c_i27___sa_g', b'c_i28___sa_g', b'c_i29___sa_g', b'c_i30___fc_g',
              b'c_i31___bd_g', b'c_i38_mst__kw_g', b'c_i43___sqs_g', b'c_i44___sqres_g', b'c_i45___sqrep_g',
              b'c_i46___sqh_g', b'c_i46___sqrev_g', b'c_i47___sqmsa_g', b'c_i48___ss_g', b'c_i49___sqa_g',
              b'c_i49___sqs_g', b'c_i50___sqaob_g', b'c_i50___sqdob_g', b'c_jets__ddw_g', b'c_jets__si_g',
              b'c_knv__kw_g', b'c_knv__sfw_g', b'c_knv__shw_g', b'c_knv__sw_g', b'c_kuro__ddw_g', b'c_kuro__si_g',
              b'c_loss_att_out_g', b'c_loss_def_out_g', b'c_m136__kw_g', b'c_m136__sfw_g', b'c_m136__shw_g',
              b'c_m136__sw_g', b'c_m14v__sw_g', b'c_m15v__ddw_g', b'c_m15v__si_g', b'c_m16__kw_g', b'c_m16__sfw_g',
              b'c_m16__shw_g', b'c_m16__sw_g', b'c_m16a1v__kw_g', b'c_m16a1v__sfw_g', b'c_m16a1v__shw_g',
              b'c_m16a1v__sw_g', b'c_m16k__kw_g', b'c_m16k__sfw_g', b'c_m16k__shw_g', b'c_m16k__sw_g', b'c_m1911__kw_g',
              b'c_m1911__sfw_g', b'c_m1911__shw_g', b'c_m1911__sw_g', b'c_m1__kw_g', b'c_m1__sfw_g', b'c_m1__shw_g',
              b'c_m1__sw_g', b'c_m1a1__kw_g', b'c_m1a1__sfw_g', b'c_m1a1__shw_g', b'c_m1a1__sw_g', b'c_m1a2__ddw_g',
              b'c_m1a2__si_g', b'c_m21v__kw_g', b'c_m21v__sfw_g', b'c_m21v__shw_g', b'c_m21v__sw_g', b'c_m249__kw_g',
              b'c_m249__sfw_g', b'c_m249__shw_g', b'c_m249__sw_g', b'c_m24__kw_g', b'c_m24__sfw_g', b'c_m24__shw_g',
              b'c_m24__sw_g', b'c_m2cg__kw_g', b'c_m2cg__sfw_g', b'c_m2cg__shw_g', b'c_m2cg__sw_g', b'c_m2v__kw_g',
              b'c_m2v__sfw_g', b'c_m2v__shw_g', b'c_m2v__sw_g', b'c_m3a3__ddw_g', b'c_m3a3__si_g', b'c_m40v__kw_g',
              b'c_m40v__sfw_g', b'c_m40v__shw_g', b'c_m40v__sw_g', b'c_m416__kw_g', b'c_m416__sfw_g', b'c_m416__shw_g',
              b'c_m416__sw_g', b'c_m48v__ddw_g', b'c_m48v__si_g', b'c_m60__kw_g', b'c_m60__sfw_g', b'c_m60__shw_g',
              b'c_m60__sw_g', b'c_m60v__kw_g', b'c_m60v__sfw_g', b'c_m60v__shw_g', b'c_m60v__sw_g', b'c_m93r__kw_g',
              b'c_m93r__sfw_g', b'c_m93r__shw_g', b'c_m93r__sw_g', b'c_m95__kw_g', b'c_m95__sfw_g', b'c_m95__shw_g',
              b'c_m95__sw_g', b'c_m95k__kw_g', b'c_m95k__sfw_g', b'c_m95k__shw_g', b'c_m95k__sw_g', b'c_m9__kw_g',
              b'c_m9__sfw_g', b'c_m9__shw_g', b'c_m9__sw_g', b'c_mac10v__kw_g', b'c_mac10v__sfw_g', b'c_mac10v__shw_g',
              b'c_mac10v__sw_g', b'c_mcs__kw_g', b'c_mcs__sfw_g', b'c_mcs__shw_g', b'c_mcs__sw_g', b'c_mg36__kw_g',
              b'c_mg36__sfw_g', b'c_mg36__shw_g', b'c_mg36__sw_g', b'c_mg3__kw_g', b'c_mg3__sfw_g', b'c_mg3__shw_g',
              b'c_mg3__sw_g', b'c_mg3k__kw_g', b'c_mg3k__sfw_g', b'c_mg3k__shw_g', b'c_mg3k__sw_g',
              b'c_minitruckv__ddw_g', b'c_minitruckv__si_g', b'c_mk14ebr__kw_g', b'c_mk14ebr__sfw_g',
              b'c_mk14ebr__shw_g', b'c_mk14ebr__sw_g', b'c_mots__kw_g', b'c_mots__sfw_g', b'c_mots__shw_g',
              b'c_mots__sw_g', b'c_mp412__kw_g', b'c_mp412__sfw_g', b'c_mp412__shw_g', b'c_mp412__sw_g',
              b'c_mp443__sfw_g', b'c_mp443__shw_g', b'c_mp443__sw_g', b'c_mst__kw_g', b'c_mst__sfw_g', b'c_mst__shw_g',
              b'c_mst__sw_g', b'c_n2k__kw_g', b'c_n2k__sfw_g', b'c_n2k__shw_g', b'c_n2k__sw_g', b'c_pbrv__ddw_g',
              b'c_pbrv__si_g', b'c_pkm__kw_g', b'c_pkm__sfw_g', b'c_pkm__shw_g', b'c_pkm__sw_g',
              b'c_pl40mmgl_40mmgl__kw_g', b'c_pl40mmsg_40mmsg__kw_g', b'c_pl9a91_9a91__kw_g', b'c_plaek_aek__kw_g',
              b'c_plair__air_ki_g', b'c_plak47v_ak47v__kw_g', b'c_plaks74u_aks74u__kw_g', b'c_plan94_an94__kw_g',
              b'c_plarm__arm_ki_g', b'c_platm_atm__kw_g', b'c_plaug_aug__kw_g', b'c_plc4_c4__kw_g',
              b'c_plf2000_f2000__kw_g', b'c_plg3_g3__kw_g', b'c_plgol_gol__kw_g', b'c_plhgr_hgr__kw_g',
              b'c_plm136_m136__kw_g', b'c_plm16_m16__kw_g', b'c_plm16a1v_m16a1v__kw_g', b'c_plm16k_m16k__kw_g',
              b'c_plm1911_m1911__kw_g', b'c_plm1_m1__kw_g', b'c_plm1a1_m1a1__kw_g', b'c_plm21v_m21v__kw_g',
              b'c_plm249_m249__kw_g', b'c_plm24_m24__kw_g', b'c_plm2cg_m2cg__kw_g', b'c_plm2v_m2v__kw_g',
              b'c_plm40v_m40v__kw_g', b'c_plm416_m416__kw_g', b'c_plm60_m60__kw_g', b'c_plm60v_m60v__kw_g',
              b'c_plm93r_m93r__kw_g', b'c_plm95_m95__kw_g', b'c_plm95k_m95k__kw_g', b'c_plm9_m9__kw_g',
              b'c_plmac10v_mac10v__kw_g', b'c_plmcs_mcs__kw_g', b'c_plmel_mel__kw_g', b'c_plmg36_mg36__kw_g',
              b'c_plmg3_mg3__kw_g', b'c_plmg3k_mg3k__kw_g', b'c_plmk14ebr_mk14ebr__kw_g', b'c_plmp412_mp412__kw_g',
              b'c_plmst_mst__kw_g', b'c_pln2k_n2k__kw_g', b'c_plpkm_pkm__kw_g', b'c_plpp2_pp2__kw_g',
              b'c_plppshv_ppshv__kw_g', b'c_plqbu88_qbu88__kw_g', b'c_plqju88_qju88__kw_g', b'c_plrpg7_rpg7__kw_g',
              b'c_plrpkv_rpkv__kw_g', b'c_pls12k_s12k__kw_g', b'c_plscar_scar__kw_g', b'c_plsea__sea_ki_g',
              b'c_plspas12_spas12__kw_g', b'c_plstav__stav_ki_g', b'c_plsv98_sv98__kw_g', b'c_plsvdv_svdv__kw_g',
              b'c_plsvu_svu__kw_g', b'c_pltt33v_tt33v__kw_g', b'c_pltveh__tveh_ki_g', b'c_plu12_u12__kw_g',
              b'c_plump_ump__kw_g', b'c_plumpk_umpk__kw_g', b'c_pluzi_uzi__kw_g', b'c_plvss_vss__kw_g',
              b'c_plxm22v_xm22v__kw_g', b'c_plxm8_xm8__kw_g', b'c_plxm8c_xm8c__kw_g', b'c_plxm8lmg_xm8lmg__kw_g',
              b'c_pp2__kw_g', b'c_pp2__sfw_g', b'c_pp2__shw_g', b'c_pp2__sw_g', b'c_ppshv__kw_g', b'c_ppshv__sfw_g',
              b'c_ppshv__shw_g', b'c_ppshv__sw_g', b'c_prtg__kw_g', b'c_qbu88__kw_g', b'c_qbu88__sfw_g',
              b'c_qbu88__shw_g', b'c_qbu88__sw_g', b'c_qju88__kw_g', b'c_qju88__sfw_g', b'c_qju88__shw_g',
              b'c_qju88__sw_g', b'c_quad__ddw_g', b'c_quad__si_g', b'c_re__da_g', b'c_rept__kw_g', b'c_rept__sfw_g',
              b'c_rept__shw_g', b'c_rept__sw_g', b'c_rok_MI28_kwi_g', b'c_rok_PBLB_kwi_g', b'c_rok__kw_g',
              b'c_rok_ah60_kwi_g', b'c_rok_ah64_kwi_g', b'c_rok_bmd3_kwi_g', b'c_rok_bmda_kwi_g', b'c_rok_cav_kwi_g',
              b'c_rok_havoc_kwi_g', b'c_rok_hmv_kwi_g', b'c_rok_m15v_kwi_g', b'c_rok_m1a2_kwi_g', b'c_rok_m3a3_kwi_g',
              b'c_rok_m48v_kwi_g', b'c_rok_quad_kwi_g', b'c_rok_t54v_kwi_g', b'c_rok_t90_kwi_g', b'c_rok_uav_kwi_g',
              b'c_rok_vodn_kwi_g', b'c_rpg7__kw_g', b'c_rpg7__sfw_g', b'c_rpg7__shw_g', b'c_rpg7__sw_g',
              b'c_rpkv__kw_g', b'c_rpkv__sfw_g', b'c_rpkv__shw_g', b'c_rpkv__sw_g', b'c_s12k__kw_g', b'c_s12k__sfw_g',
              b'c_s12k__shw_g', b'c_s12k__sw_g', b'c_scar__kw_g', b'c_scar__sfw_g', b'c_scar__shw_g', b'c_scar__sw_g',
              b'c_si40mmgl_40mmgl__kw_g', b'c_si40mmsg_40mmsg__kw_g', b'c_si9a91_9a91__kw_g', b'c_siaek_aek__kw_g',
              b'c_siair__air_ki_g', b'c_siak47v_ak47v__kw_g', b'c_siaks74u_aks74u__kw_g', b'c_sian94_an94__kw_g',
              b'c_siarm__arm_ki_g', b'c_siatm_atm__kw_g', b'c_siaug_aug__kw_g', b'c_sic4_c4__kw_g',
              b'c_sif2000_f2000__kw_g', b'c_sig3_g3__kw_g', b'c_sigol_gol__kw_g', b'c_sihgr_hgr__kw_g',
              b'c_sim136_m136__kw_g', b'c_sim16_m16__kw_g', b'c_sim16a1v_m16a1v__kw_g', b'c_sim16k_m16k__kw_g',
              b'c_sim1911_m1911__kw_g', b'c_sim1_m1__kw_g', b'c_sim1a1_m1a1__kw_g', b'c_sim21v_m21v__kw_g',
              b'c_sim249_m249__kw_g', b'c_sim24_m24__kw_g', b'c_sim2cg_m2cg__kw_g', b'c_sim2v_m2v__kw_g',
              b'c_sim40v_m40v__kw_g', b'c_sim416_m416__kw_g', b'c_sim60_m60__kw_g', b'c_sim60v_m60v__kw_g',
              b'c_sim93r_m93r__kw_g', b'c_sim95_m95__kw_g', b'c_sim95k_m95k__kw_g', b'c_sim9_m9__kw_g',
              b'c_simac10v_mac10v__kw_g', b'c_simcs_mcs__kw_g', b'c_simel_mel__kw_g', b'c_simg36_mg36__kw_g',
              b'c_simg3_mg3__kw_g', b'c_simg3k_mg3k__kw_g', b'c_simk14ebr_mk14ebr__kw_g', b'c_simp412_mp412__kw_g',
              b'c_simst_mst__kw_g', b'c_sin2k_n2k__kw_g', b'c_sipkm_pkm__kw_g', b'c_sipp2_pp2__kw_g',
              b'c_sippshv_ppshv__kw_g', b'c_siqbu88_qbu88__kw_g', b'c_siqju88_qju88__kw_g', b'c_sirpg7_rpg7__kw_g',
              b'c_sirpkv_rpkv__kw_g', b'c_sis12k_s12k__kw_g', b'c_siscar_scar__kw_g', b'c_sisea__sea_ki_g',
              b'c_sispas12_spas12__kw_g', b'c_sistav__stav_ki_g', b'c_sisv98_sv98__kw_g', b'c_sisvdv_svdv__kw_g',
              b'c_sisvu_svu__kw_g', b'c_sitt33v_tt33v__kw_g', b'c_sitveh__tveh_ki_g', b'c_siu12_u12__kw_g',
              b'c_siump_ump__kw_g', b'c_siumpk_umpk__kw_g', b'c_siuzi_uzi__kw_g', b'c_sivss_vss__kw_g',
              b'c_sixm22v_xm22v__kw_g', b'c_sixm8_xm8__kw_g', b'c_sixm8c_xm8c__kw_g', b'c_sixm8lmg_xm8lmg__kw_g',
              b'c_smol__kw_g', b'c_smol__sfw_g', b'c_smol__shw_g', b'c_smol__sw_g', b'c_spas12__kw_g',
              b'c_spas12__sfw_g', b'c_spas12__shw_g', b'c_spas12__sw_g', b'c_stgl__kw_g', b'c_stmg__kw_g',
              b'c_strl__kw_g', b'c_su__da_g', b'c_sv98__kw_g', b'c_sv98__sfw_g', b'c_sv98__shw_g', b'c_sv98__sw_g',
              b'c_svdv__kw_g', b'c_svdv__sfw_g', b'c_svdv__shw_g', b'c_svdv__sw_g', b'c_svu__kw_g', b'c_svu__sfw_g',
              b'c_svu__shw_g', b'c_svu__sw_g', b'c_t54v__ddw_g', b'c_t54v__si_g', b'c_t90__ddw_g', b'c_t90__si_g',
              b'c_ta31___ru_g', b'c_ta32___ru_g', b'c_ta33_ask__bul_g', b'c_ta34_dek__bul_g', b'c_ta35_suk__bul_g',
              b'c_ta36_rek__bul_g', b'c_ta37___bfi_g', b'c_ta38___sa_g', b'c_ta40_m1911__kw_g', b'c_ta40_m93r__kw_g',
              b'c_ta40_m9__kw_g', b'c_ta40_mp412__kw_g', b'c_ta41_rok_heli_kwi_g', b'c_ta43_deml__kw_g',
              b'c_ta44_heli_strl_diw_g', b'c_ta45__rept_hsh_g', b'c_ta48___h_g', b'c_ta48___msa_g', b'c_ta48___r_g',
              b'c_ta48___res_g', b'c_ta48___rev_g', b'c_ta49___ua_g', b'c_ta50___ua_g', b'c_tanc__kw_g',
              b'c_tanm__kw_g', b'c_trad__sfw_g', b'c_trad__sw_g', b'c_tru__ddw_g', b'c_tru__si_g', b'c_tt33v__kw_g',
              b'c_tt33v__sfw_g', b'c_tt33v__shw_g', b'c_tt33v__sw_g', b'c_u12__kw_g', b'c_u12__sfw_g', b'c_u12__shw_g',
              b'c_u12__sw_g', b'c_uav__ddw_g', b'c_uav__si_g', b'c_ump__kw_g', b'c_ump__sfw_g', b'c_ump__shw_g',
              b'c_ump__sw_g', b'c_umpk__kw_g', b'c_umpk__sfw_g', b'c_umpk__shw_g', b'c_umpk__sw_g', b'c_uzi__kw_g',
              b'c_uzi__sfw_g', b'c_uzi__shw_g', b'c_uzi__sw_g', b'c_uziv__sfw_g', b'c_uziv__sw_g', b'c_vodn__ddw_g',
              b'c_vodn__si_g', b'c_vss__kw_g', b'c_vss__sfw_g', b'c_vss__shw_g', b'c_vss__sw_g',
              b'c_vta01_win_nam02_outon_g', b'c_vta01_win_nam03_outon_g', b'c_vta01_win_nam05_outon_g',
              b'c_vta01_win_nam06_outon_g', b'c_vta04__gaz69v_ki_g', b'c_vta04__hueyv_ki_g', b'c_vta04__m15v_ki_g',
              b'c_vta04__m48v_ki_g', b'c_vta04__pbrv_ki_g', b'c_vta04__t54v_ki_g', b'c_vta05__tankv_ki_g',
              b'c_vta06__hueyv_ki_g', b'c_vta08_m2v__kw_g', b'c_win_att_out_g', b'c_win_def_out_g', b'c_xm22v__kw_g',
              b'c_xm22v__sfw_g', b'c_xm22v__shw_g', b'c_xm22v__sw_g', b'c_xm8__kw_g', b'c_xm8__sfw_g', b'c_xm8__shw_g',
              b'c_xm8__sw_g', b'c_xm8c__kw_g', b'c_xm8c__sfw_g', b'c_xm8c__shw_g', b'c_xm8c__sw_g', b'c_xm8lmg__kw_g',
              b'c_xm8lmg__sfw_g', b'c_xm8lmg__shw_g', b'c_xm8lmg__sw_g', b'deaths', b'di01_00', b'di01_01', b'di02_00',
              b'di02_01', b'di03_00', b'di03_01', b'di04_00', b'di04_01', b'dogr', b'dogt', b'dp03_00', b'dp03_01',
              b'dp04_00', b'dp04_01', b'dp07_00', b'dp07_01', b'dp08_00', b'dp08_01', b'dta03_00', b'dta03_01',
              b'dta04_00', b'dta04_01', b'elo', b'elo0', b'elo1', b'form', b'games', b'go40mmgl_00', b'go40mmgl_01',
              b'go40mmsg_00', b'go40mmsg_01', b'go9a91_00', b'go9a91_01', b'goaek_00', b'goaek_01', b'goair_00',
              b'goair_01', b'goak47v_00', b'goak47v_01', b'goaks74u_00', b'goaks74u_01', b'goan94_00', b'goan94_01',
              b'goarm_00', b'goarm_01', b'goatm_00', b'goatm_01', b'goaug_00', b'goaug_01', b'goc4_00', b'goc4_01',
              b'gof2000_00', b'gof2000_01', b'gog3_00', b'gog3_01', b'gogol_00', b'gogol_01', b'gohgr_00', b'gohgr_01',
              b'goldedition', b'gom136_00', b'gom136_01', b'gom16_00', b'gom16_01', b'gom16a1v_00', b'gom16a1v_01',
              b'gom16k_00', b'gom16k_01', b'gom1911_00', b'gom1911_01', b'gom1_00', b'gom1_01', b'gom1a1_00',
              b'gom1a1_01', b'gom21v_00', b'gom21v_01', b'gom249_00', b'gom249_01', b'gom24_00', b'gom24_01',
              b'gom2cg_00', b'gom2cg_01', b'gom2v_00', b'gom2v_01', b'gom40v_00', b'gom40v_01', b'gom416_00',
              b'gom416_01', b'gom60_00', b'gom60_01', b'gom60v_00', b'gom60v_01', b'gom93r_00', b'gom93r_01',
              b'gom95_00', b'gom95_01', b'gom95k_00', b'gom95k_01', b'gom9_00', b'gom9_01', b'gomac10v_00',
              b'gomac10v_01', b'gomcs_00', b'gomcs_01', b'gomel_00', b'gomel_01', b'gomg36_00', b'gomg36_01',
              b'gomg3_00', b'gomg3_01', b'gomg3k_00', b'gomg3k_01', b'gomk14ebr_00', b'gomk14ebr_01', b'gomp412_00',
              b'gomp412_01', b'gomst_00', b'gomst_01', b'gon2k_00', b'gon2k_01', b'gopkm_00', b'gopkm_01', b'gopp2_00',
              b'gopp2_01', b'goppshv_00', b'goppshv_01', b'goqbu88_00', b'goqbu88_01', b'goqju88_00', b'goqju88_01',
              b'gorpg7_00', b'gorpg7_01', b'gorpkv_00', b'gorpkv_01', b'gos12k_00', b'gos12k_01', b'goscar_00',
              b'goscar_01', b'gosea_00', b'gosea_01', b'gospas12_00', b'gospas12_01', b'gostav_00', b'gostav_01',
              b'gosv98_00', b'gosv98_01', b'gosvdv_00', b'gosvdv_01', b'gosvu_00', b'gosvu_01', b'gott33v_00',
              b'gott33v_01', b'gotveh_00', b'gotveh_01', b'gou12_00', b'gou12_01', b'goump_00', b'goump_01',
              b'goumpk_00', b'goumpk_01', b'gouzi_00', b'gouzi_01', b'govss_00', b'govss_01', b'goxm22v_00',
              b'goxm22v_01', b'goxm8_00', b'goxm8_01', b'goxm8c_00', b'goxm8c_01', b'goxm8lmg_00', b'goxm8lmg_01',
              b'hac_00', b'hac_01', b'hav_00', b'hav_01', b'haw_00', b'haw_01', b'hvb_00', b'hvb_01', b'hwb_00',
              b'hwb_01', b'i01_00', b'i01_01', b'i02_00', b'i02_01', b'i03_00', b'i03_01', b'i04_00', b'i04_01',
              b'i05_00', b'i05_01', b'i06_00', b'i06_01', b'i07_00', b'i07_01', b'i08_00', b'i08_01', b'i09_00',
              b'i09_01', b'i10_00', b'i10_01', b'i11_00', b'i11_01', b'i12_00', b'i12_01', b'i13_00', b'i13_01',
              b'i14_00', b'i14_01', b'i15_00', b'i15_01', b'i16_00', b'i16_01', b'i17_00', b'i17_01', b'i18_00',
              b'i18_01', b'i19_00', b'i19_01', b'i20_00', b'i20_01', b'i21_00', b'i21_01', b'i22_00', b'i22_01',
              b'i23_00', b'i23_01', b'i24_00', b'i24_01', b'i25_00', b'i25_01', b'i26_00', b'i26_01', b'i27_00',
              b'i27_01', b'i28_00', b'i28_01', b'i29_00', b'i29_01', b'i30_00', b'i30_01', b'i31_00', b'i31_01',
              b'i32_00', b'i32_01', b'i33_00', b'i33_01', b'i34_00', b'i34_01', b'i35_00', b'i35_01', b'i36_00',
              b'i36_01', b'i37_00', b'i37_01', b'i38_00', b'i38_01', b'i39_00', b'i39_01', b'i40_00', b'i40_01',
              b'i41_00', b'i41_01', b'i42_00', b'i42_01', b'i43_00', b'i43_01', b'i44_00', b'i44_01', b'i45_00',
              b'i45_01', b'i46_00', b'i46_01', b'i47_00', b'i47_01', b'i48_00', b'i48_01', b'i49_00', b'i49_01',
              b'i50_00', b'i50_01', b'kills', b'losses', b'p01_00', b'p01_01', b'p02_00', b'p02_01', b'p03_00',
              b'p03_01', b'p04_00', b'p04_01', b'p05_00', b'p05_01', b'p06_00', b'p06_01', b'p07_00', b'p07_01',
              b'p08_00', b'p08_01', b'p09_00', b'p09_01', b'p10_00', b'p10_01', b'p11_00', b'p11_01', b'p12_00',
              b'p12_01', b'p13_00', b'p13_01', b'p14_00', b'p14_01', b'p15_00', b'p15_01', b'p16_00', b'p16_01',
              b'p17_00', b'p17_01', b'p18_00', b'p18_01', b'p19_00', b'p19_01', b'p20_00', b'p20_01', b'p21_00',
              b'p21_01', b'p22_00', b'p22_01', b'p23_00', b'p23_01', b'p24_00', b'p24_01', b'p25_00', b'p25_01',
              b'p26_00', b'p26_01', b'p27_00', b'p27_01', b'p28_00', b'p28_01', b'p29_00', b'p29_01', b'p30_00',
              b'p30_01', b'p31_00', b'p31_01', b'p32_00', b'p32_01', b'p33_00', b'p33_01', b'p34_00', b'p34_01',
              b'p35_00', b'p35_01', b'p36_00', b'p36_01', b'p37_00', b'p37_01', b'p38_00', b'p38_01', b'p39_00',
              b'p39_01', b'p40_00', b'p40_01', b'pl40mmgl_00', b'pl40mmgl_01', b'pl40mmsg_00', b'pl40mmsg_01',
              b'pl9a91_00', b'pl9a91_01', b'plaek_00', b'plaek_01', b'plair_00', b'plair_01', b'plak47v_00',
              b'plak47v_01', b'plaks74u_00', b'plaks74u_01', b'plan94_00', b'plan94_01', b'plarm_00', b'plarm_01',
              b'platm_00', b'platm_01', b'plaug_00', b'plaug_01', b'plc4_00', b'plc4_01', b'plf2000_00', b'plf2000_01',
              b'plg3_00', b'plg3_01', b'plgol_00', b'plgol_01', b'plhgr_00', b'plhgr_01', b'plm136_00', b'plm136_01',
              b'plm16_00', b'plm16_01', b'plm16a1v_00', b'plm16a1v_01', b'plm16k_00', b'plm16k_01', b'plm1911_00',
              b'plm1911_01', b'plm1_00', b'plm1_01', b'plm1a1_00', b'plm1a1_01', b'plm21v_00', b'plm21v_01',
              b'plm249_00', b'plm249_01', b'plm24_00', b'plm24_01', b'plm2cg_00', b'plm2cg_01', b'plm2v_00',
              b'plm2v_01', b'plm40v_00', b'plm40v_01', b'plm416_00', b'plm416_01', b'plm60_00', b'plm60_01',
              b'plm60v_00', b'plm60v_01', b'plm93r_00', b'plm93r_01', b'plm95_00', b'plm95_01', b'plm95k_00',
              b'plm95k_01', b'plm9_00', b'plm9_01', b'plmac10v_00', b'plmac10v_01', b'plmcs_00', b'plmcs_01',
              b'plmel_00', b'plmel_01', b'plmg36_00', b'plmg36_01', b'plmg3_00', b'plmg3_01', b'plmg3k_00',
              b'plmg3k_01', b'plmk14ebr_00', b'plmk14ebr_01', b'plmp412_00', b'plmp412_01', b'plmst_00', b'plmst_01',
              b'pln2k_00', b'pln2k_01', b'plpkm_00', b'plpkm_01', b'plpp2_00', b'plpp2_01', b'plppshv_00',
              b'plppshv_01', b'plqbu88_00', b'plqbu88_01', b'plqju88_00', b'plqju88_01', b'plrpg7_00', b'plrpg7_01',
              b'plrpkv_00', b'plrpkv_01', b'pls12k_00', b'pls12k_01', b'plscar_00', b'plscar_01', b'plsea_00',
              b'plsea_01', b'plspas12_00', b'plspas12_01', b'plstav_00', b'plstav_01', b'plsv98_00', b'plsv98_01',
              b'plsvdv_00', b'plsvdv_01', b'plsvu_00', b'plsvu_01', b'pltt33v_00', b'pltt33v_01', b'pltveh_00',
              b'pltveh_01', b'plu12_00', b'plu12_01', b'plump_00', b'plump_01', b'plumpk_00', b'plumpk_01', b'pluzi_00',
              b'pluzi_01', b'plvss_00', b'plvss_01', b'plxm22v_00', b'plxm22v_01', b'plxm8_00', b'plxm8_01',
              b'plxm8c_00', b'plxm8c_01', b'plxm8lmg_00', b'plxm8lmg_01', b'rank', b'sc_assault', b'sc_award',
              b'sc_bonus', b'sc_demo', b'sc_general', b'sc_objective', b'sc_recon', b'sc_squad', b'sc_support',
              b'sc_team', b'sc_vehicle', b'score', b'si40mmgl_00', b'si40mmgl_01', b'si40mmsg_00', b'si40mmsg_01',
              b'si9a91_00', b'si9a91_01', b'siaek_00', b'siaek_01', b'siair_00', b'siair_01', b'siak47v_00',
              b'siak47v_01', b'siaks74u_00', b'siaks74u_01', b'sian94_00', b'sian94_01', b'siarm_00', b'siarm_01',
              b'siatm_00', b'siatm_01', b'siaug_00', b'siaug_01', b'sic4_00', b'sic4_01', b'sif2000_00', b'sif2000_01',
              b'sig3_00', b'sig3_01', b'sigol_00', b'sigol_01', b'sihgr_00', b'sihgr_01', b'sim136_00', b'sim136_01',
              b'sim16_00', b'sim16_01', b'sim16a1v_00', b'sim16a1v_01', b'sim16k_00', b'sim16k_01', b'sim1911_00',
              b'sim1911_01', b'sim1_00', b'sim1_01', b'sim1a1_00', b'sim1a1_01', b'sim21v_00', b'sim21v_01',
              b'sim249_00', b'sim249_01', b'sim24_00', b'sim24_01', b'sim2cg_00', b'sim2cg_01', b'sim2v_00',
              b'sim2v_01', b'sim40v_00', b'sim40v_01', b'sim416_00', b'sim416_01', b'sim60_00', b'sim60_01',
              b'sim60v_00', b'sim60v_01', b'sim93r_00', b'sim93r_01', b'sim95_00', b'sim95_01', b'sim95k_00',
              b'sim95k_01', b'sim9_00', b'sim9_01', b'simac10v_00', b'simac10v_01', b'simcs_00', b'simcs_01',
              b'simel_00', b'simel_01', b'simg36_00', b'simg36_01', b'simg3_00', b'simg3_01', b'simg3k_00',
              b'simg3k_01', b'simk14ebr_00', b'simk14ebr_01', b'simp412_00', b'simp412_01', b'simst_00', b'simst_01',
              b'sin2k_00', b'sin2k_01', b'sipkm_00', b'sipkm_01', b'sipp2_00', b'sipp2_01', b'sippshv_00',
              b'sippshv_01', b'siqbu88_00', b'siqbu88_01', b'siqju88_00', b'siqju88_01', b'sirpg7_00', b'sirpg7_01',
              b'sirpkv_00', b'sirpkv_01', b'sis12k_00', b'sis12k_01', b'siscar_00', b'siscar_01', b'sisea_00',
              b'sisea_01', b'sispas12_00', b'sispas12_01', b'sistav_00', b'sistav_01', b'sisv98_00', b'sisv98_01',
              b'sisvdv_00', b'sisvdv_01', b'sisvu_00', b'sisvu_01', b'sitt33v_00', b'sitt33v_01', b'sitveh_00',
              b'sitveh_01', b'siu12_00', b'siu12_01', b'siump_00', b'siump_01', b'siumpk_00', b'siumpk_01', b'siuzi_00',
              b'siuzi_01', b'sivss_00', b'sivss_01', b'sixm22v_00', b'sixm22v_01', b'sixm8_00', b'sixm8_01',
              b'sixm8c_00', b'sixm8c_01', b'sixm8lmg_00', b'sixm8lmg_01', b'sveteran', b'ta31_00', b'ta31_01',
              b'ta32_00', b'ta32_01', b'ta33_00', b'ta33_01', b'ta34_00', b'ta34_01', b'ta35_00', b'ta35_01',
              b'ta36_00', b'ta36_01', b'ta37_00', b'ta37_01', b'ta38_00', b'ta38_01', b'ta39_00', b'ta39_01',
              b'ta41_00', b'ta41_01', b'ta43_00', b'ta43_01', b'ta44_00', b'ta44_01', b'ta45_00', b'ta45_01',
              b'ta46_00', b'ta46_01', b'ta47_00', b'ta47_01', b'ta48_00', b'ta48_01', b'ta49_00', b'ta49_01',
              b'ta50_00', b'ta50_01', b'teamkills', b'time', b'ul_40mmsg', b'ul_40mmsmk', b'ul_aks74u', b'ul_ammb',
              b'ul_an94', b'ul_atm', b'ul_aug', b'ul_defi', b'ul_f2000', b'ul_g3', b'ul_gol', b'ul_m136', b'ul_m16',
              b'ul_m1911', b'ul_m1a1', b'ul_m249', b'ul_m2cg', b'ul_m416', b'ul_m60', b'ul_m93r', b'ul_m95', b'ul_mcs',
              b'ul_medk', b'ul_mg3', b'ul_mg36', b'ul_mk14ebr', b'ul_mots', b'ul_mp412', b'ul_mp443', b'ul_mst',
              b'ul_n2k', b'ul_pp2', b'ul_qbu88', b'ul_qju88', b'ul_rept', b'ul_s12k', b'ul_scar', b'ul_sp_ammsupp',
              b'ul_sp_assault_a', b'ul_sp_assault_r', b'ul_sp_assault_s', b'ul_sp_bodarm', b'ul_sp_buldmplus',
              b'ul_sp_coaxmg', b'ul_sp_expdmplus', b'ul_sp_expsupp', b'ul_sp_grsupp', b'ul_sp_harveharm',
              b'ul_sp_lmg_aim', b'ul_sp_lmg_r', b'ul_sp_lmg_s', b'ul_sp_medheal', b'ul_sp_medradius', b'ul_sp_sczmplus',
              b'ul_sp_shotgun_c', b'ul_sp_shotgun_s', b'ul_sp_smg_a', b'ul_sp_smg_r', b'ul_sp_smg_s', b'ul_sp_sniper_r',
              b'ul_sp_sniper_s', b'ul_sp_sprint', b'ul_sp_spscope', b'ul_sp_tnsmk', b'ul_sp_tnzm', b'ul_sp_vdamage',
              b'ul_sp_vehmosens', b'ul_sp_vreload', b'ul_spas12', b'ul_sv98', b'ul_svu', b'ul_trad', b'ul_u12',
              b'ul_ump', b'ul_uzi', b'ul_vss', b'ul_xm8', b'ul_xm8c', b'ul_xm8lmg', b'veteran', b'vta01_00',
              b'vta01_01', b'vta04_00', b'vta04_01', b'vta05_00', b'vta05_01', b'vta06_00', b'vta06_01', b'vta07_00',
              b'vta07_01', b'vta08_00', b'vta08_01', b'vta10_00', b'vta10_01', b'webvet', b'wins']
