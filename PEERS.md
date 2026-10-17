# DN42 peering inventory (AS4242420125)

Snapshot of peer sessions, moved from the server-wide notes on 2026-10-17. The live state
is authoritative: `dn42ctl peers` / `sudo birdc show protocols`. The "DN42 Active Peers"
line below is rewritten by `dn42-auto-peer.service` (`update_docs_and_git()`), which then
commits only this file.

- **DN42 Active Peers**: 40 peers established (dn42_andyyjf_fra, dn42_andyyjf_lax, dn42_baragoon_fra, dn42_flipflap_fra, dn42_flipflap_waw, dn42_headscarf_ams, dn42_iedon_ams, dn42_iedon_cdg, dn42_iedon_hkg, dn42_iedon_lon, dn42_iedon_nue, dn42_iedon_sin, dn42_iedon_sjc, dn42_iedon_waw, dn42_iris_ams01, dn42_kioubit_de2, dn42_kioubit_fr1, dn42_kioubit_uk1, dn42_kskb_ca, dn42_kskb_ch, dn42_kskb_nl, dn42_kskb_usw, dn42_maiyun_ca04, dn42_moe233_ams, dn42_nedifinita_de1, dn42_nedifinita_nl0, dn42_nyaw_tyo1, dn42_pilz, dn42_routedbits_ams, dn42_routedbits_fra, dn42_sabrina_de, dn42_whojk_hk, dn42_whojk_tw, dn42_yuyuko_fr, dn42_yuyuko_hk01, dn42_yuyuko_hk02, dn42_yuyuko_jp, dn42_yuyuko_nl, dn42_yuyuko_pl, dn42_yuyuko_us).

- Active DN42 BGP Peering: 40 sessions Established across FlipFlap, Kioubit, RoutedBits, Pilz, Sabrina, HEADSCARF175, Nedifinita, AndyYJF, Nyaw, IRIS-AS, moe233, KSKB Neo, Yuyuko Network (7 nodes), JK-Network (2 nodes: Hong Kong, Taiwan), Baragoon (Frankfurt), Maiyun (Toronto), and iEdon-Net (8 nodes):
  - `dn42_iedon_nue` (`AS4242422189`, Nürnberg `de-nue.dn42.iedon.net:32769`, port 22189, peer LL `fe80::2189:182`, our LL `fe80::125`, ~15ms, Established)
  - `dn42_iedon_ams` (`AS4242422189`, Amsterdam `nl-ams.dn42.iedon.net:41254`, port 22190, peer LL `fe80::2189:177`, our LL `fe80::125`, ~21ms, Established)
  - `dn42_iedon_cdg` (`AS4242422189`, Paris `fr-cdg.dn42.iedon.net:57008`, port 22191, peer LL `fe80::2189:176`, our LL `fe80::125`, ~18ms, Established)
  - `dn42_iedon_lon` (`AS4242422189`, London `uk-lon.dn42.iedon.net:49994`, port 22192, peer LL `fe80::2189:122`, our LL `fe80::125`, ~21ms, Established)
  - `dn42_iedon_waw` (`AS4242422189`, Warsaw `pl-waw.dn42.iedon.net:40928`, port 22193, peer LL `fe80::2189:123`, our LL `fe80::125`, ~20ms, Established)
  - `dn42_iedon_sjc` (`AS4242422189`, San Jose `us-sjc.dn42.iedon.net:45694`, port 22194, peer LL `fe80::2189:e8`, our LL `fe80::125`, ~141ms, Established)
  - `dn42_iedon_hkg` (`AS4242422189`, Hong Kong `hk-hkg.dn42.iedon.net:46615`, port 22195, peer LL `fe80::2189:120`, our LL `fe80::125`, ~197ms, Established)
  - `dn42_iedon_sin` (`AS4242422189`, Singapore `sg-sin.dn42.iedon.net:32827`, port 22196, peer LL `fe80::2189:119`, our LL `fe80::125`, ~172ms, Established)
  - `dn42_flipflap_fra` (`de-fra1.flap42.eu`, port 20263, peer LL `fe80:4263::1:27`, ~11ms, Established)
  - `dn42_flipflap_waw` (`pl-waw1.flap42.eu`, port 20266, peer LL `fe80:2263::1:15`, ~21ms, Established)
  - `dn42_kioubit_de2` (`de2.g-load.eu`, port 20391, peer LL `fe80::ade0`, ~17ms, Established)
  - `dn42_kioubit_fr1` (`fr1.g-load.eu`, port 20392, peer LL `fe80::ade0`, ~19ms, Established)
  - `dn42_kioubit_uk1` (`uk1.g-load.eu`, port 20393, peer LL `fe80::ade0`, ~16ms, Established)
  - `dn42_routedbits_fra` (`router.fra1.routedbits.com`, port 20207, peer LL `fe80::207`, our LL `fe80::125`, ~4ms, Established)
  - `dn42_routedbits_ams` (`router.ams1.routedbits.com`, port 20208, peer LL `fe80::207`, our LL `fe80::125`, ~8ms, Established)
  - `dn42_pilz` (`AS4242420663`, Amsterdam `94.142.240.36:125`, port 20663, peer LL `fe80::1312`, our LL `fe80::125`, Established)
  - `dn42_sabrina_de` (`AS4242421810`, Frankfurt `de42.sabrinaishere.party:20125`, port 21810, peer LL `fe80::1810`, our LL `fe80::125`, ~20ms, Established)
  - `dn42_headscarf_ams` (`AS4242420842`, Amsterdam `45.137.198.52:20125`, port 20842, peer LL `fe80::842`, ~5.3ms, Established)
  - `dn42_nedifinita_de1` (`AS4242420454`, Falkenstein `[2001:470:1f0b:ff:1::8f]:30125`, port 20454, peer LL `fe80::454`, ~14ms, Established)
  - `dn42_nedifinita_nl0` (`AS4242420454`, Amsterdam `143.20.154.8:30125`, port 20455, peer LL `fe80::454`, ~9.9ms, Established)
  - `dn42_andyyjf_fra` (`AS4242422921`, Frankfurt `156.226.175.73:20125`, port 22921, peer LL `fe80::2921`, ~4ms, Established)
  - `dn42_andyyjf_lax` (`AS4242422921`, Los Angeles `45.202.243.95:20125`, port 22922, peer LL `fe80::2921`, ~149ms, Established)
  - `dn42_nyaw_tyo1` (`AS4242420291`, Tokyo `jp-tyo-1.dn42.nyaw.xyz:20125`, port 20291, peer LL `fe80::fcde:3243`, our LL `fe80::fcde:319d`, Established)
  - `dn42_iris_ams01` (`AS4242421023`, Amsterdam `[2001:bc8:1640:5afb:dc00:ff:fe60:6beb]:20125`, port 21023, peer LL `fe80::1023:2`, ~17.8ms, Established)
  - `dn42_moe233_ams` (`AS4242420253`, Amsterdam `[2001:bc8:1640:5bb5:dc00:ff:fe60:c33f]:20125`, port 20253, peer LL `fe80::253`, ~18ms, Established)
  - `dn42_kskb_nl` (`AS4201271111`, Amsterdam `20.54.218.128:25026`, port 21817, peer LL `fe80::1111`, our LL `fe80::125`, ~10ms, Established)
  - `dn42_kskb_ch` (`AS4201271111`, Zurich `20.203.134.45:1029`, port 21818, peer LL `fe80::1111`, our LL `fe80::125`, ~14ms, Established)
  - `dn42_kskb_ca` (`AS4201271111`, Toronto `20.48.129.103:13057`, port 21819, peer LL `fe80::1111`, our LL `fe80::125`, ~90ms, Established)
  - `dn42_kskb_usw` (`AS4201271111`, Washington `20.190.10.218:1025`, port 21820, peer LL `fe80::1111`, our LL `fe80::125`, ~145ms, Established)
  - `dn42_yuyuko_nl` (`AS4242421117`, Amsterdam `nl01.dn42.yuyuko.com:20125`, port 21117, peer LL `fe80::1117`, our LL `fe80::125`, ~18ms, Established)
  - `dn42_yuyuko_fr` (`AS4242421117`, Paris `fr01.dn42.yuyuko.com:20125`, port 21118, peer LL `fe80::1117`, our LL `fe80::125`, ~14.3ms, Established)
  - `dn42_yuyuko_pl` (`AS4242421117`, Warsaw `pl01.dn42.yuyuko.com:20125`, port 21119, peer LL `fe80::1117`, our LL `fe80::125`, ~24.5ms, Established)
  - `dn42_yuyuko_us` (`AS4242421117`, San Jose `us01.dn42.yuyuko.com:20125`, port 21120, peer LL `fe80::1117`, our LL `fe80::125`, ~151ms, Established)
  - `dn42_yuyuko_jp` (`AS4242421117`, Tokyo `jp01.dn42.yuyuko.com:20125`, port 21121, peer LL `fe80::1117`, our LL `fe80::125`, ~242ms, Established)
  - `dn42_yuyuko_hk01` (`AS4242421117`, Hong Kong `hk01.dn42.yuyuko.com:20125`, port 21122, peer LL `fe80::1117`, our LL `fe80::125`, ~242ms, Established)
  - `dn42_yuyuko_hk02` (`AS4242421117`, Hong Kong `hk02.dn42.yuyuko.com:20125`, port 21123, peer LL `fe80::1117`, our LL `fe80::125`, ~252ms, Established)
  - `dn42_whojk_tw` (`AS4242422717`, Taiwan `tw.vm.whojk.com:23014`, port 22718, peer LL `fe80::2717`, our LL `fe80::125`, ~190ms, Established)
  - `dn42_maiyun_ca04` (`AS4242420893`, Toronto `[2603:c021:2:fe03::5]:24201`, port 20893, peer LL `fe80::893`, our LL `fe80::125`, Established, PR [myzhang1029/dn42-config-pub#25](https://github.com/myzhang1029/dn42-config-pub/pull/25) merged)
  - `dn42_baragoon_fra` (`AS4242421732`, Frankfurt `chr-fr01.as215887.net:20125`, port 20125, peer LL `fe80::1732`, our LL `fe80::125`, ~8.4ms, Established, PR [baragoon/dn42-as4242421732#35](https://github.com/baragoon/dn42-as4242421732/pull/35) merged)
  - Pending / Requested: `dn42_highdef_fra` (AS4242421080, Frankfurt `fra.peer.highdef.network:20125`, port 21080, PR jlu5/ansible-dn42#172 open, ~4.5ms), `dn42_zebreus` (AS4242421403, GitHub issue #7 opened, port 21403 reserved), `dn42_scarjit_de` (AS4242420257, Germany `dn42-router.linnenberg.dev:51820`, port 20257, GitHub issue Scarjit/dn42-setup#3 opened), `dn42_joyfulreaper_wurstcase` (AS4242420425, Wurstcase Frankfurt / Clanker NY, port 20425 reserved, request submitted via internal portal `joyfulreaper.dn42`), `dn42_0pera_de` (AS4242423077, PR #1 submitted), `dn42_natlan_fra` / `dn42_natlan_lax` (AS4242420028, provisioned via API requests 39/40), `dn42_whojk_hk` (AS4242422717, configured, upstream host unreachable).
  Exchanging ~95,000+ paths across master4 and master6 (101,470+ total across 4 BIRD tables) with Extended Next Hop (RFC 8950) active.
  Anycast DNS reachability verified (`172.20.0.53` and `fd42:d42:d42:54::1`, <18ms, 0% loss); internal domain resolution operational (`kioubit.dn42` -> `172.20.14.43`, `burble.dn42` -> `172.20.129.3`).
