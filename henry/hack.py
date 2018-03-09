# here contains must nasty hacks!!

def fix_id_error(uid):
    if uid in ID_MAP:
        return ID_MAP[uid]
    if uid in IGNORE_SET:
        return 'NA'
    return uid


IGNORE_SET = {'1302576771001', '1302576771001', '0910558795', '0910558795', '0992185888', '0992185888', '0930174717',
              '0930174717', '0906426646', '0906426646', '0912254474001', '0912254474001', '0900518843', '0900518843',
              '1708898789001', '1708898789001', '0901480778001', '0901480778001', '1203165151', '1203165151',
              '1729984507', '1729984507', '0921404016', '0921404016', '1101033250', '1101033250', '0926418753',
              '0926418753', '1302576771', '1302576771', '0704084113001',
              '0909234421001', '1905858809001', '0901094752001', '0992703294001'}

# some user id have errors when inputted. Here is a list of corrected
# ids
ID_MAP = {
 '005122776': '0905122776',
 '010072105': '0100721059',
 '01011676774': '0101167674',
 '010144199600001': '0101441996001',
 '01035917944': '0103597944',
 '01104112436001': '0104112436001',
 '029881103': '0298810103',
 '03001647848': '0301647848',
 '050015320001': '0500153220001',
 '051848552': '0951848552',
 '060005374001': '0600053474001',
 '060157979001': '0601579790001',
 '060744734001': '0960744734001',
 '063502469001': '0635024690001',
 '064186342': '0964186342',
 '070073466': '0700734666',
 '07009972821': '0700972821',
 '07010781320': '0701078132',
 '070109536001': '0701095366001',
 '070186287001': '0701786287001',
 '070275340001': '0702275340001',
 '070287619001': '0702876192001',
 '070447226': '0704447226',
 '076295617': '0762956170',
 '080077631': '0800877631',
 '08012911183': '0801298183',
 '080188969': '0801888969',
 '08030415320001': '0803041532001',
 '080417921': '0980417921',
 '090028549': '0900285490',
 '09005913013': '0905913013',
 '09006040000': '0900604000',
 '09007073557': '0900707357',
 '090072612': '0900726712',
 '09011361631': '0901131631',
 '090174528': '0901745208',
 '09017585333': '0901758523',
 '090220039': '0902200039',
 '090227768001': '0902277680001',
 '090257069': '0902570699',
 '090352485': '0903524850',
 '090393899': '0903930899',
 '09040630620013': '0904063062001',
 '09043286069': '0904328606',
 '090438035': '0900048034',
 '09044330': '0990443300',
 '09050122859': '0905122859',
 '0905255570': '0905025557',
 '`090563069': '0906563069',
 '09058273504': '0905273504',
 '090609499001': '0906094990001',
 '09061311508': '0906138508',
 '09061612598': '0961311508',
 '090622141': '0906922141',
 '090622816': '0906622816',
 '09063979557': '0906397957',
 '090646696': '0906460696',
 '090653001': '0990653001',
 '09072510496': '0907210496',
 '09073130305': '0907313035',
 '090801606': '0900801606',
 '090884485001': '0908844855001',
 '09088722552': '0908872252',
 '090923303001': '0909233030001',
 '09093306491': '0909306491',
 '091012499': '0901012499',
 '09102174901': '0102174901',
 '09103552612': '0910352612',
 '091053424': '0901053424',
 '091056543001': '0901056543001',
 '09116955001': '0901169550001',
 '091208256': '0912080256',
 '091209099': '0912090099',
 '091213850001': '0912138500001',
 '091248377': '0901248377',
 '091262526': '0910262526',
 '091312387': '0911312387',
 '091333533001': '0991333533001',
 '091346480': '0909489825',
 '091388716': '0913388716',
 '091391312': '0913919312',
 '09141055645': '0914105645',
 '091450154': '0914250154',
 '091454284001': '0914542840001',
 '09146000036': '0914600036',
 '091480778001': '0901480778001',
 '091488091': '0901480778001',
 '09158180704': '0915818074',
 '0916122328': '09161222328',
 '091639565001': '0916395650001',
 '091655963001': '0916559630001',
 '091661473': '0916661473',
 '091666142': '0916661422',
 '09169876618': '0916987618',
 '091700741001': '0917007411001',
 '09176987069': '0917698706',
 '091835943': '0918835943',
 '091871149001': '0918711490001',
 '092001326001': '0920021326',
 '092037340001': '0920373404001',
 '092086113': '0920086113',
 '09208959976': '0920895976',
 '092106968': '0921069668',
 '092156815': '0992156815',
 '092164449': '0921568150',
 '092185888': '0992185888',
 '092213131': '0922131311',
 '092233753001': '0922337530001',
 '092244996': '0922449996',
 '09230664297': '0923064297',
 '09243167603': '0924317633',
 '092510997001': '0920510997001',
 '092559749': '0925594749',
 '09256858590001': '0925686859001',
 '09276468369': '0927646836',
 '092866043001': '0992866043001',
 '092879428': '0928879428',
 '095018339001': '`0905018339001',
 '09604009464': '0960409464',
 '09703065144': '0703065144',
 '097976229001': '0907976229001',
 '098381239': '0908381239',
 '098548761001': '0908548761001',
 '09900110586': '0900110586',
 '09904080918': '0904080918',
 '09911881761001': '0911881761001',
 '09913559977001': '0991355997001',
 '09913769642': '0913769642',
 '099196485': '0991964850',
 '09922522289': '0992252289',
 '099239506001': '0999239506001',
 '099245777001': '0992457770001',
 '099261666001': '0992616660001',
 '099262722001': '0992627220001',
 '09926954470001': '0992695447001',
 '099280395001': '0992803995001',
 '099280962001': '0992809622001',
 '099612780': '0996127880',
 '099674590': '0909674590',
 '09991516689001': '0991516689001',
 '100070879': '1000708879',
 '100140014001': '1000140014001',
 '10835890001': '1000835890001',
 '110103325': '1101033250',
 '110213590': '1100213590',
 '110383691': '1103836910',
 '114919426001': '1149919426001',
 '12001361070': '1201361070001',
 '120075210': '1200775210',
 '1201599181-3': '1201591813',
 '12017906842': '1201796842',
 '12025930117': '1200593117',
 '120270018001': '1202700181',
 '12029900328': '1202990328',
 '120565123': '1205651233',
 '12310743941': '1210743941',
 '129007198001': '1290007198001',
 '130123532901': '1301235329001',
 '130582829': '1305828290',
 '130815133': '1308151333',
 '13101065299': '1310106529001',
 '131120803001': '1311208030001',
 '131772941': '1317729441',
 '13289347': '1302890347',
 '136612944': '1306612944001',
 '138646288': '1308646288',
 '17036193522001': '1703619352001',
 '170746137001': '1707461337001',
 '17078421810001': '1707842181001',
 '171035660': '1701035660',
 '171156602': '1711156602',
 '171339474': '1713394774',
 '171527735001': '1715277735001',
 '171901560': '1719015560',
 '172998457': '1729984507',
 '18023734': '1802373496',
 '180376833': '1803076833',
 '901365296': '0901365296',
 '0902130012': '0902130012',
 '903642882': '0903642882',
 '909433559': '0909433559',
 '910048099001': '0910048099001',
 '919911214': '0919911214',
 '920223476': '0920223476',
 '920804937': '0920804937',
 '921894564': '0921894564',
 '925842163': '0925842163',
 '093083657': '0930836577',
 '94318147': '0994318147',
 '956611495': '0956611495',
 '98349071': '0983049071',
 '98663177': '0986631177',
 '992723505001': '0992723505001',
 '9999': '0990054088001',
 '092002132-6': '0920021326',
}
