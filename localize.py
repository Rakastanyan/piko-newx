import json
import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path
import urllib.request

VALID_PATCH_LOCALES = ("bilingual", "zh-rCN", "zh-rTW", "en")
DEFAULT_LOCALES_DIR = Path(__file__).resolve().parent / "locales"
ISSUE_128_STRINGS_URL = (
    "https://github.com/user-attachments/files/33614621/zh-rCN-newx-strings.xml"
)

# Matches a single-line or multi-line concatenated Kotlin string literal ("..." + "...")
KOTLIN_STR_UNIT = r'"(?:\\.|[^"\\\r\n])*"'
KOTLIN_CONCAT_STR = rf'{KOTLIN_STR_UNIT}(?:\s*\+\s*{KOTLIN_STR_UNIT})*'

# Phrase-level Simplified -> Traditional terminology replacements
_S2T_PHRASES: tuple[tuple[str, str], ...] = (
    ("时间线", "動態時報"),
    ("正在关注", "跟隨中"),
    ("推荐关注", "推薦跟隨"),
    ("发现更多", "探索更多"),
    ("设置", "設定"),
    ("帖子", "貼文"),
    ("推文", "貼文"),
    ("视频", "影片"),
    ("音频", "音訊"),
    ("自定义", "自訂"),
    ("默认", "預設"),
    ("缓存", "快取"),
    ("剪贴板", "剪貼簿"),
    ("应用包名", "套件名稱"),
    ("包名", "套件名稱"),
    ("应用", "應用程式"),
    ("链接", "連結"),
    ("网址", "網址"),
    ("账号", "帳號"),
    ("用户名", "使用者名稱"),
    ("用户", "使用者"),
    ("菜单", "選單"),
    ("导航栏", "導覽列"),
    ("顶栏", "頂部列"),
    ("空间栏", "空間列"),
    ("提示条", "提示膠囊"),
    ("标签页", "分頁"),
    ("模块", "模組"),
    ("服务器", "伺服器"),
    ("网络", "網路"),
    ("屏幕", "螢幕"),
    ("分辨率", "解析度"),
    ("码率", "位元率"),
    ("字体", "字型"),
    ("高对比度", "高對比度"),
    ("调试", "偵錯"),
    ("崩溃", "當機"),
    ("日志", "日誌"),
    ("启用", "啟用"),
    ("禁用", "停用"),
    ("个人主页", "個人資料頁"),
    ("特性开关", "功能開關"),
    ("布尔型", "布林值"),
    ("布尔值", "布林值"),
    ("字符串", "字串"),
    ("文件夹", "資料夾"),
    ("缩略图", "縮圖"),
)

# Comprehensive character-level Simplified -> Traditional map
_S2T_SIMP = "万与专业东丝丢两严丧个丰临为丽举么义乌乐乔习乡书买乱争于亏云亚产亲亿仅从仑仓仪们价众优伙会伟传伤伦伪体余侧侦保信俩俭债倾假偿储儿兑党兰关兴养兽内冈册写军农冲决况冻净凄凉凌减凑几凤凭凯击函凿划刘则刚创删别利刷制剂剑剥剧剩剪副割劝办务动励劲劳势勋勾包匆区医华协单卖卢卫却卷厂厅历厉压厌厕厢厦厨县参双变叙叠叶号叹吁后吓吕吗吨听启吴吸吹吻吼员呛呜咏咔咙咛响哑哗哟唤啧啮啰啸喷嘱团园困围固国图圆圈圣场坏块坚坛坝坞坟坠垄垒垦垫垮埃埋城域培基堂堆堕堡堤堪堰堵塌塑塔塘塞填境墅墓墙增墨壁壤壮声壳壶处备复够头夸夹夺奋奖奥妆妇妈妖妙妥妨妮妹妻姆姐姑姓委姿威娃娄娇娘娜娟娠娥娱娶婆婉婚婴婶媒媚媳嫁嫂嫉嫌嫡嫩孙学孪宁它宅宇守安宋完宏宗官宙定宛宜宝实宠审客宣室宪宫害宴宵家容宽宾宿寂寄密寇富寒寓寝寞察寡寨寸对寻导寿封射将尊小少尔尖尘尚尝尤就尴尺尼尽尾尿局屁层居届屈屋尸屎屏屑展屉属屠屡履屯山岁岂岗岘岚岛岩岭岳岸峡峰峻崇崎崔崖崩崭嵌巅巡工左巧巨巩巫差己已巳巴巷币市布帅帆师希帐帕帖帘帚帛帝带帧席帮常帽幅幌幔幕平年并幸幻幼幽广庄庆庇床序庐库应底店庙庚府庞废度座庭康庸廉廊廓廖延廷建开异弃弄弊式引弓弗弘弛弟张弥弦弧弩弯弱弹强归当录形彤彦彩彪彬彭彰影役彻彼往征径待很徊律徐徒得徘徙御循微德徽心必忆忌忍忏志忘忙忠忧快忱念忽怀态怂怅怆怜思怠怡急性怨怪怯总恋恐恒恕恢恤恨恩恬恭息恰恳恶恼悄悉悍悔悖悚悟悠患悦您悬悯悲悴悸悼情惊惑惕惜惟惠惦惧惨惩惫惭惮惯惰想惶惹愁愈愉意愕愚感愤愧愿慈慌慎慑慕慢慧慨慰慷憋憎憔憨憩懂懈懊懒戈戏成我戒或战截戮戴户房所扁扇手才扎扑扒打扔托扛扣执扩扫扬扭扮扯扰扳扶批扼找承技抄把抑抒抓投抖抗折抚抛抠抡抢护报担披抬抱抵抹押抽拂拆拇拉拌拍拎拐拒拓拔拖拗拘拙拚招拜拟拢拣拥拦拧拨择括拭拮拯拱拳拴拷拼拽拾拿持挂指按挎挑挖挚挛挝挞挟挠挡挣挤挥挨挪挫振挺挽捂捅捆捉捍捎捏捐捕捞损捡换捣捧据捶捷捻掀掂扫授掉掌掏排掖掘掠探接控推掩措掬掷掸掺揉揍描提插揖扬换握揣揩揪揭援揽搀搁搂搅搏搓搔搜搞搪搬搭携摄摆摇摈摊摔摘摩摸摹摺撇撑撒撕撞撤撩撬播撮撰撵撷撸撺撼擀擂擅操擎擦攀攒攘支收改攻放政故效敌敏救敕敖教敛敝敞敢散敦敬数敲整敷文斋斌斐斑斓斗料斜斟斤斥斧斩断斯新方施旁旅旋族旗无既日旦旧旨早旬旭旱时旷旺昂昆昇昌明昏易星映春昧昨昭是昼显晃晋晌晒晓晔晕晖晚晤晦晨普景晰晴晶智晾暂暇暑暖暗暝暧暨暮暴暹曙曜曝曲更曹曼曾替最月有朋服朗望朝期木未末本札术朱朴朵机朽杀杂权杆杈杉李杏材村杓杖杜束杠条来杨杭杯杰松板极构析林果枝枢枣枪枫枭枯架枷柄柏某柑柒染柔柜柠查柬柯柱柳柴柿栅标栈栋栏树栓栖栗校株样核根格栽桂桃框案桌桐桑桓桔档桥桦桨桩梦检棉棋棍棒棕棘棚棠森棱棵棹棺椅植椎椒椭椰椴椿楂楔楚楠楣楫业极楷楸楹楼概榄榆榈榉榔榕榛榜榨榫榭榴榷榻槁槃槌枪槐槛槟槽模样横樯樱樵樽橄橇橘橙橡橱橹檀檄檐檬欠次欢欣欧欲欺款歇歉歌止正此步武歧歪死歼殃殆残陨殓殖殡殴段殷杀壳毁毅母每毒比毕9毛毡毫毯氏民气氢氩氦氧氨氰氯氮水永汁求汇汉汗汛江池污汤汪汰汹汽沃沈沉沙沛沟没沦沧沪沫河沸油治沼沽沾沿泄泉泊泌法泛泡波泣泥注泪泰泳泵泻泼泽洁洋洒洗洛洞津洪洲活洽派流浅浆浇浊测济浏浑浓浙浚浜浦浩浪浮浴海浸涂消涉涌涎涓涕涛涝涟涡涣涤润涧涨涩涮涯液涵涸淀淆淋淌淑淘淡淤净沦淫淬淮深淳混淹添清渊渍渐渔渗渚减9渠渡渣渤渥温测渭港渴游渺湃湄湍湖湘湛湾湿溃溅溉源溜溢溪溯溶溺灭灯灰灵灶灾灿炉点炼炽烁烂烃烈烘烦烧烫烬热焕焖爱爷牵牺状犹狂狐狗狙狠狡独狭狮狱猎猪猫献猴率玉王玛玩玫环现玲玻珊珍珠班球理琉琐瑶瓜瓢瓣瓦瓶瓷甘甚甜生产用甩甫甬田由甲申电男甸画畅界畏畔留畜略畦番异疏疑疗疯疲疼疾病痕痛痴痒瘫瘾登白百皂的皆皇皮皱皿盆盈益盏盐监盒盔盖盗盘盛盟目盯盲直相盼盾省眉看真眠眨眩眯眶眷眸眺眼着睁睛睡督睦睫睬睹瞄瞎瞒瞧瞩瞪瞬矛矢矣知矩矫短矮石矾矿码砂砌砍研砖砚破砸础硅硒硕硝硫硬确碍碎碑碗碘碟碧碰碱碳碴碾磁磅磊磋磐磕磨磷磺礁示礼社祀祁祖祝神祟祠祥票祯祷祸禁禄禅福离禽禾秃秀私秋种科秒秘租秤秦秧秩积称秸移秽稀税程稍稔稗稚稠稳稻稼稽稿穆穗穴究穷空穿突窃窄窈窍窑窒窕窖窗窘窜窝窟窥立竖站竞竟章竣童竭端竹竺竿笃笆笈笋笑笔笙笛笞笠笤笥符笨第笺笼等筋筏筐筑筒答策筛筝筠筹签简箍箔箕算管箩箫箭箱箴箸节范篆篇篓篙篡篮篱篷簇籍米类籽粉粒粕粗粘粹精糊糕糖糙糜粪糟糠粮系紧紫累繁红纤约级纪纫纬纯纱纲纳纵纶纷纸纹纺纽线练组绅细织终绊绍绎经绑绒结绕绘给绚络绝统继绩绪续绳维绵绷绸综绿缀缄缅缆缉缎缓缔缕编缘缚缝缠缩缭缴缸缺罐网罕罗罚罢罩罪置署羊美羞群羽翁翅翌翔翘翻翼耀老考者而耍耐耕耗耳耶耻耽耿聂聊聋职联聘聚聪肃肆肉肌肚肝肠股肢肤肥肩肯育肺肾肿胀胁胃胆背胎胖胜胞胡胶胸能脂脆脉脊脏脐脑脓脖脚脱脸脾腊腋腔腕腥腮腰腹腺腻腾腿膀臂臣自臭至致舌舍舒舔舟航般舰舱舵舶船艇良艰色艳艺节芒芦芬芭芯花芳芹芽苇苍苏苗苛苞苟若苦英茂范茄茅茎茧茶荆草荐荒荡荣荤荧药荷荼莉庄莎莓莅莫莱莲获莹莺莽菇菊菌菜菠菩华菱菲萄萌萍萎萝萤营萦萧萨落著葛葡董葬葱葵蒂蒋蒙蒜蒲蒸蓄蓉蓝蓬蔑蔓蔗蔚蔡蔫蔬蔷蕉蕊蕴蕾薄薪薯藉藏藐藓藤藻蘑虎虏虑虫虹虽虾蚀蚁蚂蚊蚕蛇蛋蛙蛛蛮蜂蜗蜜蜡蝇蝉螺蟹血行衍街衙衡衣补表衫衬衰衷袁袋袍袒袖袜被袭袱裁裂装裆裕裤裳裸裹制裾褂褐褒襁襟见观规觅视觇览觉觊觋觌觎觏觐觑角解触言誉誊计订讣认讥讦讧讨让讪讫训议讯记讲讳讴讵讶讷许讹论讼讽设访诀证诂诃评诅识诈诉诊诋词诏译诒诓诔试诖诗诘诙诚诛诜话诞诟诠诡询诣诤该详诧诨诩诫诬语诮误诰诱诲诳说诵诶请诸诹诺读诼诽课诿谀谁谂调谄谅谆谇谈谊谋谌谍谎谏谐谑谒谓谔谕谖谗谘谙谚谛谜谝谟谠谡谢谣谤谥谦谧谨谩谪谫谬谭谮谯谰谱谲谳谴谵谷豆岂竖丰象豪猪貌贝贞负财贡贫货贩贪贯责贮贯贱贲贳贴贵贶贷贸费贺贻贼贽贾贿赀赁赂赃资赅赆赇赈赉赊赋赌赍赎赏赐赔赕赖赘赙赚赛赜赝赞赠赡赢赣赤赦赫走赴赵赶起趁越趋趟趣足跃跌跑距跟迹跨路跳践踏踢踩踪身躲躺车轧轨轩转轭轮软轰轱轲轳轴轵轶轷轸轹轺轻轼载轾轿辀辁辂较辄辅辆辇辈辉辊辋辌辍辎辏辐辑辒输辔辕辖辗辘辙辚辛辜辞辟辣辨辩辫辰辱边辽达迁迂迄迅过迈迎运近还这进远违连迟迫述迷迹追退送适逃逆选逊透逐递途逗通逛逝速造逢连逮逸逻逼遇遍道遗遭遮遵避邀邓那邦邪邮邻郁郊郎郑部郭都鄙酉酌配酒酝酸酿醉醒采释里重野量金鉴针钉釜针钓钙钛钝钞钟钠钢钣钤钥钦钧钨钩钮钱钳钻铁铃铅铆铜铝铡铣铭铬银铸铺链销锁锄锅锈锋锌锐错锚锡锣锤锦键锯锰锹锻镀镇镊镜镭镰镶长门闪闭问闯闰闲间闷闸闹闺闻闼闽闾阀阁阂阅阉阎阐阑阔阕阖阙闯队阳阴阵阶际陆陇陈陋陌降限陕院除陨险陪陵陶陷隅隆随隐隔隘隙障难雀雁雄雅集雇雌雏雕雨雪雯雳零雷雹雾需霄霆震霉霍霎霏霓霖霜霞露霸霹青靓靖静非靠靡面革靴靶鞋鞍鞘鞠鞭韦韧韩音韵韶页顶顷项顺须顼顽顾顿颀颁颂颃预颅领颇颈颉颊颌颖颏颐频颓颔颖颗题颚颛颜额颞颟颠颡颢颤颦颧风飑飒飓飕飘飙飞食饥饭饮饯饰饱饲饴饵饶饷饺饼饿馁馅馆馈馋馍馏馐馑馒首香馨马驭驮驯驰驱驳驴驶驹驻驼驾驿骂骄骅骆骇骋验骏骑骗骚骤骨骰骷骸髓高髟髯髻鬃松胡鬓闹鬼魁魂魄魅魏魔鱼鲁鲍鲜鲤鲨鲸鳄鸟鸠鸡鸣鸥鸦鸭鸳鸯鸵鸽鸿鹃鹅鹄鹏鹤鹰鹿麦麸麻黄黍黎黏黑黔默黛黜点黝黠黯鼎鼓鼠鼻齐齿龄龙龚龛龟"
_S2T_TRAD = "萬與專業東絲丟兩嚴喪個豐臨為麗舉麼義烏樂喬習鄉書買亂爭於虧雲亞產親億僅從侖倉儀們價眾優夥會偉傳傷倫偽體餘側偵保信倆儉債傾假償儲兒兌黨蘭關興養獸內岡冊寫軍農衝決況凍淨淒涼凌減湊幾鳳憑凱擊函鑿劃劉則剛創刪別利刷製劑劍剝劇剩剪副割勸辦務動勵勁勞勢勳勾包匆區醫華協單賣盧衛卻卷廠廳歷厲壓厭廁廂廈廚縣參雙變敘疊葉號嘆籲後嚇呂嗎噸聽啟吳吸吹吻吼員嗆嗚詠咔嚨嚀響啞嘩喲喚嘖嚙囉嘯噴囑團園困圍固國圖圓圈聖場壞塊堅壇壩塢墳墜壟壘墾墊垮埃埋城域培基堂堆墮堡堤堪堰堵塌塑塔塘塞填境墅墓牆增墨壁壤壯聲殼壺處備復夠頭誇夾奪奮獎奧妝婦媽妖妙妥妨妮妹妻姆姐姑姓委姿威娃婁嬌娘娜娟娠娥娛娶婆婉婚嬰嬸媒媚媳嫁嫂嫉嫌嫡嫩孫學孿寧它宅宇守安宋完宏宗官宙定宛宜寶實寵審客宣室憲宮害宴宵家容寬賓宿寂寄密寇富寒寓寢寞察寡寨寸對尋導壽封射將尊小少爾尖塵尚嘗尤就尷尺尼盡尾尿局屁層居屆屈屋屍屎屏屑展屜屬屠屢履屯山歲豈崗峴嵐島岩嶺岳岸峽峰峻崇崎崔崖崩嶄嵌巔巡工左巧巨鞏巫差己已巳巴巷幣市布帥帆師希帳帕帖簾帚帛帝帶幀席幫常帽幅幌幔幕平年並幸幻幼幽廣莊慶庇床序廬庫應底店廟庚府龐廢度座庭康庸廉廊廓廖延廷建開異棄弄弊式引弓弗弘弛弟張彌弦弧弩彎弱彈強歸當錄形彤彥彩彪彬彭彰影役徹彼往征徑待很徊律徐徒得徘徙禦循微德徽心必憶忌忍懺志忘忙忠憂快忱念忽懷態慫悵愴憐思怠怡急性怨怪怯總戀恐恆恕恢恤恨恩恬恭息恰懇惡惱悄悉悍悔悖悚悟悠患悅您懸憫悲悴悸悼情驚惑惕惜惟惠惦懼慘懲憊慚憚慣惰想惶惹愁愈愉意愕愚感憤愧願慈慌慎懾慕慢慧慨慰慷憋憎憔憨憩懂懈懊懶戈戲成我戒或戰截戮戴戶房所扁扇手才扎撲扒打扔托扛扣執擴掃揚扭扮扯擾扳扶批扼找承技抄把抑抒抓投抖抗折撫拋摳掄搶護報擔披抬抱抵抹押抽拂拆拇拉拌拍拎拐拒拓拔拖拗拘拙拚招拜擬攏揀擁攔擰撥擇括拭拮拯拱拳拴拷拼拽拾拿持掛指按挎挑挖摯攣撾撻挾撓擋掙擠揮挨挪挫振挺挽捂捅捆捉捍捎捏捐捕撈損撿換搗捧據捶捷捻掀掂掃授掉掌掏排掖掘掠探接控推掩措掬擲撣摻揉揍描提插揖揚換握揣揩揪揭援攬攙擱摟攪搏搓搔搜搞搪搬搭攜攝擺搖擯攤摔摘摩摸摹摺撇撐撒撕撞撤撩撬播撮撰攆擷擼攛撼擀擂擅操擎擦攀攢攘支收改攻放政故效敵敏救敕敖教斂敝敞敢散敦敬數敲整敷文齋斌斐斑斕鬥料斜斟斤斥斧斬斷斯新方施旁旅旋族旗無既日旦舊旨早旬旭旱時曠旺昂昆昇昌明昏易星映春昧昨昭是晝顯晃晉晌曬曉曄暈暉晚晤晦晨普景晰晴晶智晾暫暇暑暖暗暝曖暨暮暴暹曙曜曝曲更曹曼曾替最月有朋服朗望朝期木未末本札術朱樸朵機朽殺雜權桿杈杉李杏材村杓杖杜束槓條來楊杭杯傑松板極構析林果枝樞棗槍楓梟枯架枷柄柏某柑柒染柔櫃檸查柬柯柱柳柴柿柵標棧棟欄樹栓棲栗校株樣核根格栽桂桃框案桌桐桑桓桔檔橋樺槳樁夢檢棉棋棍棒棕棘棚棠森稜棵棹棺椅植椎椒橢椰椴椿楂楔楚楠楣楫業極楷楸楹樓概欖榆櫚櫸榔榕榛榜榨榫榭榴榷榻槁槃槌槍槐檻檳槽模樣橫檣櫻樵樽橄橇橘橙橡櫥櫓檀檄簷檬欠次歡欣歐欲欺款歇歉歌止正此步武歧歪死殲殃殆殘隕殮殖殯毆段殷殺殼毀毅母每毒比畢9毛氈毫毯氏民氣氫氬氦氧氨氰氯氮水永汁求匯漢汗汛江池污湯汪汰洶汽沃沈沉沙沛溝沒淪滄滬沫河沸油治沼沽沾沿洩泉泊泌法泛泡波泣泥注淚泰泳泵瀉潑澤潔洋灑洗洛洞津洪洲活洽派流淺漿澆濁測濟瀏渾濃浙浚浜浦浩浪浮浴海浸塗消涉湧涎涓涕濤澇漣渦渙滌潤澗漲澀涮涯液涵涸澱淆淋淌淑淘淡淤淨淪淫淬淮深淳混淹添清淵漬漸漁滲渚減9渠渡渣渤渥溫測渭港渴遊渺湃湄湍湖湘湛灣濕潰濺漑源溜溢溪溯溶溺滅燈灰靈灶災燦爐點煉熾爍爛烴烈烘煩燒燙燼熱煥燜愛爺牽犧狀猶狂狐狗狙狠狡獨狹獅獄獵豬貓獻猴率玉王瑪玩玫環現玲玻珊珍珠班球理琉瑣瑤瓜瓢瓣瓦瓶瓷甘甚甜生產用甩甫甬田由甲申電男甸畫暢界畏畔留畜略畦番異疏疑療瘋疲疼疾病痕痛癡癢癱癮登白百皂的皆皇皮皺皿盆盈益盞鹽監盒盔蓋盜盤盛盟目盯盲直相盼盾省眉看真眠眨眩瞇眶眷眸眺眼著睜睛睡督睦睫睬睹瞄瞎瞞瞧矚瞪瞬矛矢矣知矩矯短矮石礬礦碼砂砌砍研磚硯破砸礎矽硒碩硝硫硬確礙碎碑碗碘碟碧碰鹼碳碴碾磁磅磊磋磐磕磨磷磺礁示禮社祀祁祖祝神祟祠祥票禎禱禍禁祿禪福離禽禾禿秀私秋種科秒秘租秤秦秧秩積稱秸移穢稀稅程稍稔稗稚稠穩稻稼稽稿穆穗穴究窮空穿突竊窄窈竅窯窒窕窖窗窘竄窩窟窺立豎站競竟章竣童竭端竹竺竿篤笆笈筍笑筆笙笛笞笠笤笥符笨第箋籠等筋筏筐築筒答策篩箏筠籌簽簡箍箔箕算管籮簫箭箱箴箸節範篆篇簍篙篡籃籬篷簇籍米類籽粉粒粕粗粘粹精糊糕糖糙糜糞糟糠糧係緊紫累繁紅纖約級紀紉緯純紗綱納縱綸紛紙紋紡紐線練組紳細織終絆紹繹經綁絨結繞繪給絢絡絕統繼績緒續繩維綿繃綢綜綠綴緘緬纜緝緞緩締縷編緣縛縫纏縮繚繳缸缺罐網罕羅罰罷罩罪置署羊美羞群羽翁翅翌翔翹翻翼耀老考者而耍耐耕耗耳耶恥耽耿聶聊聾職聯聘聚聰肅肆肉肌肚肝腸股肢膚肥肩肯育肺腎腫脹脅胃膽背胎胖勝胞胡膠胸能脂脆脈脊臟臍腦膿脖腳脫臉脾臘腋腔腕腥腮腰腹腺膩騰腿膀臂臣自臭至致舌捨舒舔舟航般艦艙舵舶船艇良艱色艷藝節芒蘆芬芭芯花芳芹芽葦蒼蘇苗苛苞苟若苦英茂範茄茅莖繭茶荊草薦荒蕩榮葷螢藥荷荼莉莊莎莓蒞莫萊蓮獲瑩鶯莽菇菊菌菜菠菩華菱菲萄萌萍萎蘿螢營縈蕭薩落著葛葡董葬蔥葵蒂蔣蒙蒜蒲蒸蓄蓉藍蓬蔑蔓蔗蔚蔡蔫蔬薔蕉蕊蘊蕾薄薪薯藉藏藐蘚藤藻蘑虎虜慮蟲虹雖蝦蝕蟻螞蚊蠶蛇蛋蛙蛛蠻蜂蝸蜜蠟蠅蟬螺蟹血行衍街衙衡衣補表衫襯衰衷袁袋袍袒袖襪被襲袱裁裂裝襠裕褲裳裸裹製裾褂褐褒襁襟見觀規覓視覘覽覺覬覡覿覦覯覲覷角解觸言譽謄計訂訃認譏訐訌討讓訕訖訓議訊記講諱謳詎訝訥許訛論訟諷設訪訣證詁訶評詛識詐訴診詆詞詔譯詒誆誄試詿詩詰詼誠誅詵話誕詬詮詭詢詣諍該詳詫諢詡誡誣語誚誤誥誘誨誑說誦誒請諸諏諾讀諑誹課諉諛誰諗調諂諒諄誶談誼謀諶諜謊諫諧謔謁謂諤諭諼讒諮諳諺諦謎諞謨讜謖謝謠謗諡謙謐謹謾謫譾謬譚譖譙讕譜譎讞譴譫谷豆豈豎豐象豪豬貌貝貞負財貢貧貨販貪貫責貯貫賤賁貰貼貴貺貸貿費賀貽賊贄賈賄貲賃賂贓資賅贐賕賑賚賒賦賭齎贖賞賜賠賧賴贅賻賺賽賾贗贊贈贍贏贛赤赦赫走赴趙趕起趁越趨趟趣足躍跌跑距跟跡跨路跳踐踏踢踩蹤身躲躺車軋軌軒轉軛輪軟轟軲軻轤軸軹軼軤軫轢軺輕軾載輊轎輈輇輅較輒輔輛輦輩輝輥輞輬輟輜輳輻輯輼輸轡轅轄輾轆轍轔辛辜辭闢辣辨辯辮辰辱邊遼達遷迂迄迅過邁迎運近還這進遠違連遲迫述迷跡追退送適逃逆選遜透逐遞途逗通逛逝速造逢連逮逸邏逼遇遍道遺遭遮遵避邀鄧那邦邪郵鄰鬱郊郎鄭部郭都鄙酉酌配酒醞酸釀醉醒採釋裡重野量金鑑針釘釜針釣鈣鈦鈍鈔鐘鈉鋼鈑鈐鑰欽鈞鎢鉤鈕錢鉗鑽鐵鈴鉛鉚銅鋁鍘銑銘鉻銀鑄鋪鏈銷鎖鋤鍋鏽鋒鋅銳錯錨錫鑼錘錦鍵鋸錳鍬鍛鍍鎮鑷鏡鐳鐮鑲長門閃閉問闖閏閒間悶閘鬧閨聞闥閩閭閥閣閡閱閹閻闡闌闊闋闔闕闖隊陽陰陣階際陸隴陳陋陌降限陝院除隕險陪陵陶陷隅隆隨隱隔隘隙障難雀雁雄雅集僱雌雛雕雨雪雯靂零雷雹霧需霄霆震霉霍霎霏霓霖霜霞露霸霹青靚靖靜非靠靡面革靴靶鞋鞍鞘鞠鞭韋韌韓音韻韶頁頂頃項順須頊頑顧頓頎頒頌頏預顱領頗頸頡頰頜穎頦頤頻頹頷穎顆題顎顓顏額顳顢顛顙顥顫顰顴風颮颯颶颼飄飆飛食飢飯飲餞飾飽飼飴餌饒餉餃餅餓餒餡館饋饞饃餾饈饉饅首香馨馬馭馱馴馳驅駁驢駛駒駐駝駕驛罵驕驊駱駭騁驗駿騎騙騷驟骨骰骷骸髓高髟髯髻鬃鬆鬍鬢鬧鬼魁魂魄魅魏魔魚魯鮑鮮鯉鯊鯨鱷鳥鳩雞鳴鷗鴉鴨鴛鴦鴕鴿鴻鵑鵝鵠鵬鶴鷹鹿麥麩麻黃黍黎黏黑黔默黛黜點黝黠黯鼎鼓鼠鼻齊齒齡龍龔龕龜"
_S2T_TABLE = str.maketrans(_S2T_SIMP, _S2T_TRAD)


def _load_remote_zh_cn_strings() -> dict[str, str]:
    """Attempt to fetch the 472-string zh-rCN XML from Issue #128 during online builds."""
    try:
        req = urllib.request.Request(
            ISSUE_128_STRINGS_URL,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        with urllib.request.urlopen(req, timeout=12) as resp:
            xml_bytes = resp.read()
        root = ET.fromstring(xml_bytes.decode("utf-8"))
        result: dict[str, str] = {}
        for elem in root.findall("string"):
            name = elem.attrib.get("name")
            if name:
                result[name] = "".join(elem.itertext())
        if len(result) >= 50:
            print(f"Downloaded {len(result)} strings from Issue #128 attachment")
            return result
    except Exception as exc:
        print(f"Note: Using bundled localization dictionary ({exc})")
    return {}


def to_traditional_chinese(text: str, region: str = "TW") -> str:
    """Convert Simplified Chinese UI strings to Traditional Chinese (zh-rTW / zh-rHK)."""
    result = text
    for simp, trad in _S2T_PHRASES:
        result = result.replace(simp, trad)
    if region == "HK":
        result = (
            result.replace("動態時報", "時間線")
            .replace("貼文", "帖文")
            .replace("使用者", "用戶")
            .replace("字型", "字體")
        )
    # Replace Chinese double quotes with corner brackets for Traditional Chinese UI
    result = result.translate(_S2T_TABLE)
    result = result.translate(_S2T_TABLE)
    result = re.sub(r"“([^”]*)”", r"「\1」", result)
    return result


# Smart English-to-Chinese UI translator for any new upstream keys or patch descriptions
_EN_EXACT_MAP: dict[str, str] = {
    "OK": "确定",
    "Cancel": "取消",
    "Save": "保存",
    "Default": "默认",
    "Timeline": "时间线",
    "Content": "内容与过滤",
    "Appearance": "外观与主题",
    "Posts and media": "帖子与媒体",
    "Links": "链接与分享",
    "Navigation": "导航与侧栏",
    "Advanced": "高级与调试",
    "Backup and restore": "备份与恢复",
    "Translation": "翻译",
    "Translator": "翻译引擎",
    "Theme": "主题",
    "Photos": "照片",
    "Videos": "视频",
    "Most recent": "最新",
    "Popular": "热门",
    "Ask every time": "每次询问",
    "Original": "原图",
    "Large": "大图",
    "Medium": "中图",
    "Small": "小图",
    "Highest bitrate": "最高码率",
    "Lowest bitrate": "最低码率",
}

_EN_WORD_REPLACEMENTS: tuple[tuple[str, str], ...] = (
    ("NewX: ", "NewX: "),
    ("Removes ", "移除"),
    ("Remove ", "移除"),
    ("Hides ", "隐藏"),
    ("Hide ", "隐藏"),
    ("Shows ", "显示"),
    ("Show ", "显示"),
    ("Enables ", "启用"),
    ("Enable ", "启用"),
    ("Disables ", "禁用"),
    ("Disable ", "禁用"),
    ("Filters ", "过滤"),
    ("Filter ", "过滤"),
    ("Customizes ", "自定义"),
    ("Customize ", "自定义"),
    ("Custom ", "自定义"),
    ("Restores ", "恢复"),
    ("Restore ", "恢复"),
    ("Adds ", "添加"),
    ("Add ", "添加"),
    ("Deletes ", "删除"),
    ("Delete ", "删除"),
    ("Clears ", "清除"),
    ("Clear ", "清除"),
    ("Bypasses ", "绕过"),
    ("Bypass ", "绕过"),
    ("Allows ", "允许"),
    ("Allow ", "允许"),
    ("Prevents ", "防止"),
    ("Replace ", "替换"),
    ("Replaces ", "替换"),
    ("promoted posts", "推广帖子"),
    ("sponsored posts", "赞助帖子"),
    ("advertisements", "广告"),
    ("ads", "广告"),
    ("timelines", "时间线"),
    ("timeline", "时间线"),
    ("Who to follow", "推荐关注"),
    ("Topics to follow", "推荐话题"),
    ("Creators to follow", "推荐创作者"),
    ("Discover more", "发现更多"),
    ("sensitive media", "敏感媒体"),
    ("media downloads", "媒体下载"),
    ("download button", "下载按钮"),
    ("downloads", "下载"),
    ("download", "下载"),
    ("premium upsell", "Premium 会员推广"),
    ("Premium upsell", "Premium 会员推广"),
    ("Spaces bar", "Spaces 空间栏"),
    ("spaces bar", "Spaces 空间栏"),
    ("new post pill", "新帖子悬浮提示条"),
    ("new post button", "发帖悬浮按钮"),
    ("post dividers", "帖子分隔线"),
    ("poll results", "投票结果"),
    ("profile", "个人主页"),
    ("settings", "设置"),
    ("Settings", "设置"),
    ("package name", "应用包名"),
    ("app name", "应用名称"),
    ("font", "字体"),
    ("blur", "模糊效果"),
    ("translator", "翻译器"),
    ("translation", "翻译"),
    ("tracking", "追踪参数"),
    ("share", "分享"),
    ("drawer", "侧边抽屉栏"),
    ("navigation bar", "底部导航栏"),
    ("cache", "缓存"),
    ("thumbnails", "缩略图"),
    ("video player", "视频播放器"),
    ("videos", "视频"),
    ("video", "视频"),
    ("images", "图片"),
    ("photos", "照片"),
    ("posts", "帖子"),
    ("post", "帖子"),
)


def translate_english_ui_text(en_text: str) -> str:
    """Fallback translator so any newly added upstream string or patch is localized."""
    stripped = en_text.strip()
    if not stripped:
        return en_text
    if stripped in _EN_EXACT_MAP:
        return _EN_EXACT_MAP[stripped]
    # If already contains Chinese characters, return as-is
    if re.search(r"[\u4e00-\u9fff]", stripped):
        return stripped

    prefix = ""
    body = stripped
    if body.startswith("NewX: "):
        prefix = "NewX: "
        body = body.removeprefix("NewX: ")

    translated = body
    for src, dst in _EN_WORD_REPLACEMENTS:
        translated = re.sub(rf"\b{re.escape(src)}\b", dst, translated, flags=re.IGNORECASE)

    if re.search(r"[\u4e00-\u9fff]", translated):
        # Clean up extra spaces between Chinese characters
        translated = re.sub(r"([\u4e00-\u9fff])\s+([\u4e00-\u9fff])", r"\1\2", translated)
        translated = re.sub(r"([\u4e00-\u9fff])\s+([\u4e00-\u9fff])", r"\1\2", translated)
        return f"{prefix}{translated}"

    return en_text


def _escape_kotlin_string(value: str) -> str:
    return (
        value.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("$", "\\$")
    )


def _format_bilingual(cn_text: str, tw_text: str, separator: str = " / ") -> str:
    if cn_text == tw_text:
        return cn_text
    if cn_text.startswith("NewX: ") and tw_text.startswith("NewX: "):
        cn_body = cn_text.removeprefix("NewX: ")
        tw_body = tw_text.removeprefix("NewX: ")
        if cn_body == tw_body:
            return cn_text
        return f"NewX: {cn_body}{separator}{tw_body}"
    return f"{cn_text}{separator}{tw_text}"


def _parse_android_strings(xml_path: Path) -> dict[str, tuple[str, dict[str, str]]]:
    tree = ET.parse(xml_path)
    root = tree.getroot()
    entries: dict[str, tuple[str, dict[str, str]]] = {}
    for elem in root.findall("string"):
        name = elem.attrib.get("name")
        if name:
            text = "".join(elem.itertext())
            entries[name] = (text, dict(elem.attrib))
    return entries


def _write_strings_xml(
    entries: list[tuple[str, str, dict[str, str]]],
    target_xml_path: Path,
) -> None:
    target_xml_path.parent.mkdir(parents=True, exist_ok=True)
    root = ET.Element("resources")
    for _, text, attrib in entries:
        elem = ET.SubElement(root, "string", attrib)
        elem.text = text
    ET.indent(root, space="    ")
    tree = ET.ElementTree(root)
    tree.write(target_xml_path, encoding="utf-8", xml_declaration=True)
    target_xml_path.write_text(
        target_xml_path.read_text(encoding="utf-8") + "\n",
        encoding="utf-8",
    )


def inject_android_strings(
    piko_directory: Path,
    patch_locale: str = "bilingual",
    locales_dir: Path = DEFAULT_LOCALES_DIR,
) -> list[Path]:
    """Inject Simplified & Traditional Chinese NewX strings.xml into Piko resources (including default values/ fallback)."""
    addresources_dir = piko_directory / "patches/src/main/resources/addresources"
    base_xml = addresources_dir / "values/newx/strings.xml"

    local_cn_xml = locales_dir / "values-zh-rCN/newx/strings.xml"
    local_tw_xml = locales_dir / "values-zh-rTW/newx/strings.xml"
    local_hk_xml = locales_dir / "values-zh-rHK/newx/strings.xml"

    cn_dict: dict[str, str] = {}
    attrib_dict: dict[str, dict[str, str]] = {}

    # 1. Load remote Issue #128 472-string XML if available (in GitHub Actions)
    remote_cn = _load_remote_zh_cn_strings()
    cn_dict.update(remote_cn)

    # 2. Merge bundled local zh-rCN dictionary
    if local_cn_xml.is_file():
        for k, (v, attr) in _parse_android_strings(local_cn_xml).items():
            cn_dict[k] = v
            attrib_dict[k] = attr

    tw_overrides: dict[str, str] = {}
    if local_tw_xml.is_file():
        for k, (v, _) in _parse_android_strings(local_tw_xml).items():
            tw_overrides[k] = v

    hk_overrides: dict[str, str] = {}
    if local_hk_xml.is_file():
        for k, (v, _) in _parse_android_strings(local_hk_xml).items():
            hk_overrides[k] = v

    # 3. Read base English values/newx/strings.xml if present
    base_entries: dict[str, tuple[str, dict[str, str]]] = {}
    if base_xml.is_file():
        base_entries = _parse_android_strings(base_xml)

    all_keys: list[str] = (
        list(base_entries.keys()) if base_entries else list(cn_dict.keys())
    )

    cn_final: list[tuple[str, str, dict[str, str]]] = []
    tw_final: list[tuple[str, str, dict[str, str]]] = []
    hk_final: list[tuple[str, str, dict[str, str]]] = []

    for key in all_keys:
        base_text, base_attr = base_entries.get(key, ("", {"name": key}))
        attr = dict(base_attr or attrib_dict.get(key, {"name": key}))
        if attr.get("translatable") == "false":
            cn_val = base_text or cn_dict.get(key, "")
            tw_val = cn_val
            hk_val = cn_val
        else:
            cn_val = cn_dict.get(key) or translate_english_ui_text(base_text)
            tw_val = tw_overrides.get(key) or to_traditional_chinese(cn_val, region="TW")
            hk_val = hk_overrides.get(key) or to_traditional_chinese(cn_val, region="HK")

        cn_final.append((key, cn_val, attr))
        tw_final.append((key, tw_val, attr))
        hk_final.append((key, hk_val, attr))

    injected_files: list[Path] = []
    locale_targets: list[tuple[str, list[tuple[str, str, dict[str, str]]]]] = [
        ("values-zh-rCN", cn_final),
        ("values-zh", cn_final),
        ("values-b+zh+Hans", cn_final),
        ("values-zh-rTW", tw_final),
        ("values-b+zh+Hant", tw_final),
        ("values-zh-rHK", hk_final),
    ]

    for folder_name, entries in locale_targets:
        target_xml = addresources_dir / folder_name / "newx/strings.xml"
        _write_strings_xml(entries, target_xml)
        injected_files.append(target_xml)

    # Also localize default values/newx/strings.xml when patch_locale != 'en'
    # so base APKs without split locale configs still show Chinese UI!
    if patch_locale != "en" and base_xml.is_file():
        default_entries = tw_final if patch_locale == "zh-rTW" else cn_final
        _write_strings_xml(default_entries, base_xml)
        injected_files.append(base_xml)

    return injected_files


def _extract_concat_string(expr: str) -> str:
    parts = re.findall(r'"((?:\\.|[^"\\\r\n])*)"', expr)
    raw = "".join(parts)
    return raw.replace('\\"', '"').replace("\\n", "\n").replace("\\\\", "\\")


def localize_patch_options(
    piko_directory: Path,
    patch_locale: str = "bilingual",
    locales_dir: Path = DEFAULT_LOCALES_DIR,
) -> int:
    """Localize all NewX patch names, descriptions, and option titles/descriptions in Kotlin sources."""
    if patch_locale not in VALID_PATCH_LOCALES:
        raise ValueError(
            f"Invalid patch_locale '{patch_locale}'. Expected one of {VALID_PATCH_LOCALES}"
        )

    if patch_locale == "en":
        return 0

    i18n_file = locales_dir / "patches_i18n.json"
    i18n_data = (
        json.loads(i18n_file.read_text(encoding="utf-8"))
        if i18n_file.is_file()
        else {}
    )
    raw_patches: dict[str, dict[str, dict[str, str]]] = i18n_data.get("patches", {})
    raw_options: dict[str, dict[str, dict[str, str]]] = i18n_data.get("options", {})

    # Build case-insensitive lookup maps
    patches_ci = {k.lower(): v for k, v in raw_patches.items()}
    options_ci = {k.lower(): v for k, v in raw_options.items()}

    newx_kt_dir = piko_directory / "patches/src/main/kotlin/app/crimera/patches/newx"
    if not newx_kt_dir.is_dir():
        return 0

    def format_localized_pair(cn_val: str, tw_val: str) -> str:
        if patch_locale == "zh-rCN":
            return cn_val
        if patch_locale == "zh-rTW":
            return tw_val
        return _format_bilingual(cn_val, tw_val)

    def translate_patch_name_and_desc(en_name: str, en_desc: str | None) -> tuple[str, str | None]:
        entry = patches_ci.get(en_name.lower())
        if entry:
            cn_name = entry.get("zh-rCN", {}).get("name", en_name)
            tw_name = entry.get("zh-rTW", {}).get("name", to_traditional_chinese(cn_name))
            cn_desc = entry.get("zh-rCN", {}).get("description")
            tw_desc = entry.get("zh-rTW", {}).get("description")
        else:
            cn_name = translate_english_ui_text(en_name)
            tw_name = to_traditional_chinese(cn_name)
            cn_desc = translate_english_ui_text(en_desc) if en_desc else None
            tw_desc = to_traditional_chinese(cn_desc) if cn_desc else None

        loc_name = format_localized_pair(cn_name, tw_name)
        loc_desc = format_localized_pair(cn_desc, tw_desc) if (cn_desc and tw_desc) else None
        return loc_name, loc_desc

    def translate_option_title_and_desc(en_title: str, en_desc: str | None) -> tuple[str, str | None]:
        entry = options_ci.get(en_title.lower())
        if entry:
            cn_title = entry.get("zh-rCN", {}).get("title", en_title)
            tw_title = entry.get("zh-rTW", {}).get("title", to_traditional_chinese(cn_title))
            cn_desc = entry.get("zh-rCN", {}).get("description")
            tw_desc = entry.get("zh-rTW", {}).get("description")
        else:
            cn_title = translate_english_ui_text(en_title)
            tw_title = to_traditional_chinese(cn_title)
            cn_desc = translate_english_ui_text(en_desc) if en_desc else None
            tw_desc = to_traditional_chinese(cn_desc) if cn_desc else None

        loc_title = format_localized_pair(cn_title, tw_title)
        loc_desc = format_localized_pair(cn_desc, tw_desc) if (cn_desc and tw_desc) else None
        return loc_title, loc_desc

    updated_files = 0
    patch_pattern = re.compile(
        rf'(\bname\s*=\s*)({KOTLIN_CONCAT_STR})'
        rf'(?:(\s*,\s*\bdescription\s*=\s*)({KOTLIN_CONCAT_STR}))?'
    )
    option_pattern = re.compile(
        rf'(\btitle\s*=\s*)({KOTLIN_CONCAT_STR})'
        rf'(?:(\s*,\s*\bdescription\s*=\s*)({KOTLIN_CONCAT_STR}))?'
    )

    for kt_file in sorted(newx_kt_dir.rglob("*.kt")):
        original = kt_file.read_text(encoding="utf-8")

        def _patch_repl(m: re.Match) -> str:
            en_name = _extract_concat_string(m.group(2))
            en_desc = _extract_concat_string(m.group(4)) if m.group(4) else None
            loc_name, loc_desc = translate_patch_name_and_desc(en_name, en_desc)
            out = f'{m.group(1)}"{_escape_kotlin_string(loc_name)}"'
            if m.group(3) and m.group(4):
                final_desc = loc_desc or en_desc or ""
                out += f'{m.group(3)}"{_escape_kotlin_string(final_desc)}"'
            return out

        def _option_repl(m: re.Match) -> str:
            en_title = _extract_concat_string(m.group(2))
            en_desc = _extract_concat_string(m.group(4)) if m.group(4) else None
            loc_title, loc_desc = translate_option_title_and_desc(en_title, en_desc)
            out = f'{m.group(1)}"{_escape_kotlin_string(loc_title)}"'
            if m.group(3) and m.group(4):
                final_desc = loc_desc or en_desc or ""
                out += f'{m.group(3)}"{_escape_kotlin_string(final_desc)}"'
            return out

        modified = patch_pattern.sub(_patch_repl, original)
        modified = option_pattern.sub(_option_repl, modified)

        if modified != original:
            kt_file.write_text(modified, encoding="utf-8")
            updated_files += 1

    return updated_files


def apply_chinese_localization(
    piko_directory: Path,
    patch_locale: str | None = None,
    locales_dir: Path = DEFAULT_LOCALES_DIR,
) -> dict[str, int]:
    """Apply both Android bilingual resources (zh-rCN/zh-rTW/zh-rHK + default values) and patch option localization."""
    resolved_locale = patch_locale or os.environ.get("PIKO_PATCH_LOCALE", "bilingual")
    injected = inject_android_strings(
        piko_directory,
        patch_locale=resolved_locale,
        locales_dir=locales_dir,
    )
    updated_kt = localize_patch_options(
        piko_directory,
        patch_locale=resolved_locale,
        locales_dir=locales_dir,
    )
    print(
        f"Applied Chinese localization: injected {len(injected)} Android locale files "
        f"(including zh-rCN/zh-rTW/zh-rHK and default fallback), localized {updated_kt} Kotlin patch files (mode={resolved_locale})"
    )
    return {
        "injected_locale_files": len(injected),
        "localized_kotlin_files": updated_kt,
    }
