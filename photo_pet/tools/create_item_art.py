"""Original editable vector product illustrations; all animal motifs are Niangao."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from niangao.life.catalog import BY_ID
OUT=Path(__file__).resolve().parents[1]/"assets/items";OUT.mkdir(parents=True,exist_ok=True)
INK="#342d2b";MINT="#b8dbca";PINK="#f0c0bc";YELLOW="#f8dfa0";CREAM="#fffaf0";BROWN="#715443"
def path(d,fill="none",stroke=INK,width=4):return f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{width}" stroke-linecap="round" stroke-linejoin="round"/>'
def rect(x,y,w,h,fill,rx=12):return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{INK}" stroke-width="4"/>'
def ellipse(x,y,rx,ry,fill):return f'<ellipse cx="{x}" cy="{y}" rx="{rx}" ry="{ry}" fill="{fill}" stroke="{INK}" stroke-width="4"/>'
def cat(x=70,y=73,s=.65):
    return f'<g transform="translate({x} {y}) scale({s})">'+path("M6 32 L4 4 L28 16 Q48 7 66 16 L90 4 L86 35 Q102 72 72 87 Q48 100 20 87 Q-10 73 6 32",CREAM)+path("M7 30 L7 8 L30 20 Q48 12 67 20 L87 8 L86 35 Q86 58 65 59 L53 53 L46 26 L34 50 Q17 65 7 47",BROWN)+ellipse(29,45,6,7,"#8ebed9")+ellipse(68,45,6,7,"#8ebed9")+path("M43 61 Q49 57 54 61 L49 68 Z",PINK)+f'<circle cx="57" cy="60" r="3.5" fill="{BROWN}"/>'+path("M49 68 L49 74 M49 74 Q43 79 39 74 M49 74 Q54 79 59 74")+path("M8 65 L-6 61 M10 71 L-3 75 M86 65 L100 61 M85 72 L98 77")+"</g>"
def heart(x,y,s=1,fill=PINK):return f'<g transform="translate({x} {y}) scale({s})">'+path("M0 7 C-12 -4 -28 13 0 31 C28 13 12 -4 0 7",fill)+"</g>"
def star(x,y,s=1):return f'<g transform="translate({x} {y}) scale({s})">'+path("M0 -17 L5 -5 L18 -4 L9 5 L12 18 L0 11 L-12 18 L-9 5 L-18 -4 L-5 -5 Z",YELLOW)+"</g>"
def fish(x,y,s=1,color=MINT):return f'<g transform="translate({x} {y}) scale({s})">'+path("M-31 0 Q-10 -24 19 -10 L37 -23 L33 0 L37 23 L19 10 Q-10 24 -31 0 Z",color)+f'<circle cx="-15" cy="-2" r="3" fill="{INK}"/>'+path("M8 -10 Q0 0 8 10")+"</g>"
def bottle(color=MINT,pattern=""):
    return rect(63,24,66,20,CREAM,5)+path("M69 44 L69 59 Q45 69 45 88 L45 145 Q45 163 64 163 L128 163 Q147 163 147 145 L147 88 Q147 69 123 59 L123 44 Z",color)+pattern
def bowl(water=False):
    return path("M24 100 Q20 157 54 163 L138 163 Q170 158 168 100 Z",MINT if water else PINK)+ellipse(96,99,72,23,CREAM)+ellipse(96,100,58,13,"#a6d8e6" if water else "#bd9877")+cat(76,126,.40)
def art(id):
    if id in ("milk","kitten_food","food","senior_food"):
        color={"milk":CREAM,"kitten_food":PINK,"food":MINT,"senior_food":"#c9bdda"}[id]
        return path("M48 30 L144 30 L151 158 Q94 170 41 158 Z",color)+path("M48 43 L144 43 M46 146 Q94 153 147 146")+cat(66,68,.65)+(star(143,40,.55) if id=="kitten_food" else fish(96,136,.35,YELLOW))
    if id=="fish":return fish(95,100,1.6,YELLOW)+star(145,42,.4)
    if id=="freeze_dried":return rect(29,90,53,52,YELLOW)+rect(86,49,55,54,CREAM)+rect(116,111,49,45,"#e8c599")+path("M42 105 L58 104 M99 64 L118 63 M128 125 L142 128")
    if id=="wet_food":return rect(37,68,118,83,PINK)+ellipse(96,67,59,17,CREAM)+ellipse(96,62,19,7,YELLOW)+cat(65,82,.6)
    if id=="cat_strip":return path("M65 20 L116 29 L126 157 L75 169 Z",PINK)+path("M65 36 L118 43 M73 151 L125 142")+fish(95,99,.6,YELLOW)
    if id in ("happy_snack","energy_snack","clean_snack"):
        color={"happy_snack":PINK,"energy_snack":YELLOW,"clean_snack":MINT}[id]
        return rect(40,38,112,126,color)+cat(62,62,.7)+(heart(132,46,.55) if id=="happy_snack" else star(134,47,.5) if id=="energy_snack" else path("M130 29 L130 47 M121 38 L139 38"))
    if id=="wand":return path("M31 168 L107 56",BROWN,INK,9)+path("M107 56 Q151 19 159 72")+ellipse(155,96,18,29,PINK)+path("M154 76 L155 120 M142 87 L155 96 L170 91")
    if id in ("ball","bell_ball"):
        return ellipse(96,105,61,61,YELLOW if id=="bell_ball" else MINT)+path("M50 67 Q104 74 129 151 M51 145 Q91 98 151 81")+ (ellipse(97,106,19,19,PINK)+path("M84 105 L110 105 M96 106 L96 119") if id=="bell_ball" else cat(63,72,.65))
    if id=="mouse":return ellipse(94,111,54,32,"#c6b9a4")+ellipse(68,82,17,19,PINK)+ellipse(91,80,16,17,PINK)+path("M143 112 Q173 99 166 68",PINK)+ellipse(48,116,5,5,PINK)+f'<circle cx="63" cy="105" r="4" fill="{INK}"/>'+path("M101 111 L110 107 L119 111 L110 115 Z",CREAM)
    if id=="feather":return path("M44 162 Q70 105 139 33",stroke=BROWN,width=6)+path("M61 126 Q39 67 86 47 Q108 19 151 26 Q152 80 114 102 Z",MINT)+path("M67 119 L90 68 M89 99 L132 62")
    if id=="catnip":return fish(95,107,1.5,PINK)+path("M57 87 L63 94 M65 80 L70 87 M105 102 L109 110")
    if id in ("bowl","food_bowl","water_bowl"):return bowl(id=="water_bowl")
    if id=="water_fountain":
        return path("M49 75 L39 55 L65 65 Q96 54 128 65 L154 55 L144 76 L153 146 Q151 163 135 164 L57 164 Q40 161 39 146 Z",MINT)+ellipse(96,80,50,17,CREAM)+ellipse(96,82,40,11,"#a6d8e6")+path("M91 76 L91 47 Q91 33 107 33 Q119 33 119 43",stroke=INK,width=8)+path("M120 44 Q131 57 120 72",stroke="#7dbbcf",width=6)+cat(74,108,.45)+ellipse(123,132,8,10,"#8ebed9")
    if id=="water_bottle":return bottle("#b5dce4",cat(67,89,.6))+path("M94 76 Q73 103 94 113 Q116 103 94 76","#82b8d1")
    if id=="brush":return path("M81 106 L67 160 Q84 177 98 160 L113 109 Z",PINK)+ellipse(103,71,49,55,MINT)+path("M74 56 L81 61 M90 43 L96 50 M110 43 L116 50 M127 57 L132 64 M73 78 L81 84 M96 69 L102 76 M118 78 L124 84 M89 94 L96 101")
    if id=="wash_basin":return path("M25 89 Q26 153 60 165 L135 165 Q169 153 168 89 Z",PINK)+ellipse(96,87,72,20,"#b5dce4")+ellipse(55,78,17,17,CREAM)+ellipse(78,63,23,23,CREAM)+ellipse(114,74,21,21,CREAM)+cat(74,109,.45)
    if id=="bed":return ellipse(96,118,76,43,MINT)+ellipse(96,112,56,28,CREAM)+heart(96,99,.7)
    if id=="scratcher":return path("M26 110 L141 81 L167 122 L50 156 Z",BROWN)+path("M26 110 L26 132 L50 171 L167 137 L167 122",YELLOW)+path("M45 114 L145 91 M50 123 L151 100 M57 131 L157 109",stroke="#bd9877")
    if id=="rug":return path("M34 54 Q23 40 15 55 L22 164 Q42 154 57 168 L164 143 Q173 122 162 111 L164 30 Q150 36 137 24 Z",YELLOW)+cat(56,60,.85)+path("M22 163 L20 173 M38 166 L36 177 M55 168 L54 178")
    if id=="plant":return path("M59 116 L69 164 L122 164 L133 116 Z",PINK)+path("M96 118 L96 60",stroke=BROWN,width=5)+ellipse(75,75,24,14,MINT)+ellipse(113,59,21,15,"#91bd9b")+ellipse(98,36,17,23,MINT)
    if id=="lamp":return ellipse(96,160,48,12,MINT)+path("M96 149 L96 82",stroke=BROWN,width=9)+path("M48 84 L64 35 L128 35 L145 84 Z",YELLOW)+star(96,60,.6)
    if id=="tree":return ellipse(98,167,66,13,MINT)+path("M68 159 L68 60 M129 159 L129 30",stroke=BROWN,width=14)+rect(28,52,82,18,YELLOW)+rect(94,24,70,18,PINK)+rect(46,119,104,18,MINT)+cat(98,70,.5)
    if id=="hammock":return path("M29 43 L29 162 M163 43 L163 162",stroke=BROWN,width=9)+path("M29 73 Q97 144 163 73 L148 121 Q96 163 44 121 Z",PINK)+path("M29 73 L54 82 M163 73 L139 83")
    if id=="litter":return rect(27,85,138,73,MINT)+ellipse(96,89,65,20,YELLOW)+path("M45 94 L52 95 M70 83 L77 86 M91 98 L98 96 M116 84 L122 86 M139 96 L146 94")+cat(78,113,.4)
    if id=="bow":return path("M88 84 Q37 35 30 62 L30 137 Q45 156 88 106 M104 84 Q157 34 163 62 L163 137 Q149 156 104 106",PINK)+ellipse(96,96,18,22,YELLOW)
    if id=="scarf":return path("M33 71 Q96 37 159 73 L151 98 Q98 73 42 106 Z",MINT)+path("M121 96 L146 156 L115 168 L94 108 Z",PINK)+path("M120 165 L124 175 M130 162 L134 173 M141 158 L145 169")
    if id=="crown":return path("M32 57 L70 94 L96 41 L124 93 L164 57 L149 145 L47 145 Z",YELLOW)+star(96,112,.55)+ellipse(32,52,6,6,PINK)+ellipse(96,35,6,6,PINK)+ellipse(164,52,6,6,PINK)
    if id=="freeze_age":return bottle("#d0c0df",cat(67,82,.6))+path("M96 75 L96 113 M79 83 L112 105 M79 105 L112 83",stroke=CREAM,width=5)
    if id=="kitten_candy":return path("M61 72 L25 62 L29 119 L61 111 M130 72 L166 62 L162 119 L130 111",PINK)+ellipse(96,94,42,38,YELLOW)+cat(72,71,.48)
    if id=="comfort":return rect(36,50,120,113,MINT,26)+heart(96,80,1.1)
    if id=="cleaner":return path("M71 36 L137 36 L137 55 L110 61 L110 78 L72 78 Z",PINK)+path("M112 58 L136 83",stroke=INK,width=7)+bottle(MINT,star(96,119,.7))
    if id=="health_kit":return rect(30,69,132,98,CREAM)+path("M69 67 L69 43 L123 43 L123 67",MINT)+cat(66,87,.65)+heart(143,55,.45,MINT)
    if id=="affection":return rect(36,78,120,85,PINK)+rect(29,62,134,29,YELLOW)+path("M96 65 L96 163",stroke=INK,width=10)+heart(96,30,.8)
    if id in ("stars","petals"):return bottle("#d0c0df" if id=="stars" else "#e5c4ca",star(95,116,.9) if id=="stars" else heart(96,105,1))
    if id=="material_pack":return rect(42,31,112,136,CREAM)+path("M57 31 L57 166")+cat(69,68,.7)+path("M128 37 L166 131",stroke=PINK,width=9)
    raise ValueError("Missing unique item illustration: "+id)
for id in BY_ID:
    svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="192" height="192" viewBox="0 0 192 192">{art(id)}</svg>'
    (OUT/(id+".svg")).write_text(svg,encoding="utf-8")
print("Unique item illustrations:",len(BY_ID))
