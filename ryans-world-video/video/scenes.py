"""Every scene of the video: narration (what the voice says) and the visuals cued to it.

A cue like at="sixty billion" makes that element appear when the narrator says those words.
Narration here is the source of truth for the voiceover; build.py exports it for ElevenLabs.
"""
import os

from engine import (BLUE, GREEN, H, LINE, MUTED, PANEL, RED, W, WHITE, YELLOW, Counter, Rect, Ring,
                    Scene, Shot, Stamp, Strike, Text)

HERE = os.path.dirname(os.path.abspath(__file__))
SHOTS = os.path.join(HERE, "..", "assets", "screens")


def shot(name):
    return os.path.join(SHOTS, name)


def money(v, dp=0, suffix="M"):
    return f"${v:,.{dp}f}{suffix}"


def headline(text, y=200, size=78, color=WHITE, at=0, **kw):
    return Text(text, W / 2, y, size=size, color=color, at=at, maxw=1600, **kw)


def label(text, x, y, at=0, color=MUTED, size=30, anchor="mm", **kw):
    return Text(text, x, y, size=size, weight="Bold", color=color, at=at, anchor=anchor, shadow=False, **kw)


def after(at, d):
    """A cue d seconds after another cue."""
    if isinstance(at, (int, float)):
        return at + d
    if isinstance(at, tuple):
        return (at[0], at[1] + d)
    return (at, d)


def card(x, y, w, h, title, value, at, color=WHITE, value_size=64, outline=None, title_color=MUTED, out=None,
         value_y=None):
    return [
        Rect(x, y, w, h, outline=outline, at=at, out=out),
        Text(title, x + w / 2, y + 62, size=28, weight="Bold", color=title_color, at=after(at, 0.1),
             shadow=False, maxw=w - 60, out=out),
        Text(value, x + w / 2, value_y or y + h / 2 + 30, size=value_size, color=color, maxw=w - 60,
             at=after(at, 0.2), out=out),
    ]


# ---------------------------------------------------------------- the board
BX, BY, BW = 190, 215, 1540
ROW_H, HEAD_H = 175, 84
COL_LABEL, COL_CLAIM, COL_FOUND = BX + 50, BX + 520, BX + 990
ROWS = [("PERSONAL FORTUNE", "$100 MILLION"), ("STARTED AT AGE", "3"), ("MADE FROM", "TOY VIDEOS")]
FOUND = [("$100M+ GROSS\n~$50M KEPT (BUSINESS)\nRYAN'S SHARE: NOT PUBLIC", YELLOW), ("TRUE", GREEN), ("MOSTLY LICENSING\n& MERCHANDISE", YELLOW)]


def board(row_cues, found_cues=None, head_at=0, title_at=0):
    els = [
        Text("THE BOARD", BX, BY - 70, size=54, color=YELLOW, anchor="lm", at=title_at),
        Rect(BX, BY, BW, HEAD_H + ROW_H * 3, fill=(18, 22, 30), outline=LINE, at=head_at),
        Rect(BX, BY, BW, HEAD_H, fill=(30, 36, 48), radius=18, shadow=False, at=head_at),
        label("THE CLAIM", COL_CLAIM, BY + HEAD_H / 2, at=head_at, anchor="lm", color=RED),
    ]
    if found_cues:
        els.append(label("WHAT I FOUND", COL_FOUND, BY + HEAD_H / 2, at=found_cues[0], anchor="lm", color=GREEN))
    for i, ((lab, claim), cue) in enumerate(zip(ROWS, row_cues)):
        y = BY + HEAD_H + ROW_H * i
        els += [
            Rect(BX + 20, y + ROW_H - 2, BW - 40, 2, fill=LINE, radius=0, shadow=False, at=cue),
            label(lab, COL_LABEL, y + ROW_H / 2, at=cue, anchor="lm", size=28),
            Text(claim, COL_CLAIM, y + ROW_H / 2, size=58, anchor="lm", at=cue, anim="left"),
        ]
        if found_cues:
            txt, col = FOUND[i]
            els.append(Text(txt, COL_FOUND, y + ROW_H / 2, size=34 if "\n" in txt else 58, anchor="lm",
                            color=col, align="left", at=found_cues[i], anim="right"))
    return els


def row_y(i):
    return BY + HEAD_H + ROW_H * i + ROW_H / 2


# ---------------------------------------------------------------- scenes
S = []

# 1 HOOK -------------------------------------------------------------------
S.append(Scene("01_hook_claim", "", (
    "Search \"Ryan's World net worth\" and you'll get the same number again and again: one hundred million dollars. "
    "A kid who started reviewing toys at three years old, now worth a hundred million."),
    src="celebritynetworth.com", whip=False, els=[
        Shot(shot("cnw.png"), at=0, anim="fade",
             focus=[("the same number", (180, 105, 1100, 335))],
             marks=[("hl", "one hundred million", (408, 160, 656, 212)),
                    ("ring", "now worth", (408, 160, 656, 212))]),
    ]))

S.append(Scene("02_hook_views", "", (
    "His channel has more than sixty billion views. Millions of people have seen that hundred-million figure and believed it."),
    src="YouTube / Social Blade, 2026", els=[
        Shot(shot("channel.png"), at=0, focus=[(0.6, (250, 270, 1110, 470))],
             marks=[("hl", "sixty billion", (550, 330, 676, 352))], out="Millions of people"),
        Counter(W / 2, H / 2 - 40, 60, lambda v: f"{v:,.0f},000,000,000+", at="Millions of people", dur=1.0,
                size=130),
        label("TOTAL CHANNEL VIEWS", W / 2, H / 2 + 80, at=("Millions of people", 0.3), size=34, color=YELLOW),
    ]))

S.append(Scene("03_hook_doubt", "", (
    "But I went through the Forbes lists, the toy sales, the ad rates and the laws on who gets a child's money, "
    "and I ran the numbers myself. And the hundred million doesn't mean what you think it means."), els=[
        *card(150, 300, 380, 300, "SOURCE 1", "FORBES\nLISTS", "the Forbes lists", value_size=54, out="doesn't mean"),
        *card(570, 300, 380, 300, "SOURCE 2", "TOY\nSALES", "the toy sales", value_size=54, out="doesn't mean"),
        *card(990, 300, 380, 300, "SOURCE 3", "AD\nRATES", "the ad rates", value_size=54, out="doesn't mean"),
        *card(1410, 300, 380, 300, "SOURCE 4", "CHILD\nLAWS", "the laws", value_size=54, out="doesn't mean"),
        headline("I RAN THE NUMBERS MYSELF", y=760, size=64, color=YELLOW, at="ran the numbers", out="doesn't mean"),
        Text("$100,000,000", W / 2, H / 2 - 60, size=150, at=("doesn't mean", 0.1), anim="fade"),
        Stamp("≠ WHAT YOU THINK", W / 2, H / 2 + 110, at=("doesn't mean", 0.5), size=84),
    ]))

S.append(Scene("04_title", "", "", hold=3.2, glow=RED, els=[
    Text("DID RYAN'S WORLD", W / 2, 420, size=110, at=0.1, anim="rise"),
    Text("REALLY MAKE", W / 2, 545, size=110, at=0.35, anim="rise"),
    Text("$100 MILLION?", W / 2, 690, size=150, color=YELLOW, at=0.7, anim="pop", sfx="hit"),
]))

S.append(Scene("05_promise", "", (
    "By the end of this video you'll know where that number came from, what it leaves out, and how much of it "
    "could actually belong to Ryan. And I'll give you my own estimate at the end."), els=[
        Text("1", 300, 330, size=90, color=YELLOW, at="where that number"),
        Text("WHERE THE $100M CAME FROM", 380, 330, size=58, anchor="lm", at="where that number", anim="left"),
        Text("2", 300, 480, size=90, color=YELLOW, at="what it leaves out"),
        Text("WHAT IT LEAVES OUT", 380, 480, size=58, anchor="lm", at="what it leaves out", anim="left"),
        Text("3", 300, 630, size=90, color=YELLOW, at="how much of it"),
        Text("HOW MUCH COULD BE RYAN'S", 380, 630, size=58, anchor="lm", at="how much of it", anim="left"),
        Text("+ MY OWN ESTIMATE AT THE END", W / 2, 820, size=44, color=BLUE, at="my own estimate",
             bg=(20, 40, 70), pad=(36, 18), outline=BLUE),
    ]))

# 2 WHY IT MATTERS ---------------------------------------------------------
S.append(Scene("06_board", "01 · The claim", (
    "First, here's what the claim would mean. Here's the board. "
    "If that's true, a child would be one of the richest creators alive, richer than most movie stars, "
    "and every dollar of it would be his."), els=[
        *board(["the board", ("the board", 0.6), ("the board", 1.2)], head_at=0.15, title_at=0.15),
        Stamp("EVERY DOLLAR HIS?", 1440, row_y(0), at="every dollar", size=54, angle=-6),
    ]))

S.append(Scene("07_three_numbers", "01 · The claim", (
    "That last part is what matters, because there are really three different numbers hiding in this story: "
    "how much the brand sold, how much the family business earned, and how much belongs to Ryan. "
    "Most headlines mix all three."), els=[
        headline("3 DIFFERENT NUMBERS", y=190, at="three different numbers"),
        *card(170, 330, 500, 380, "NUMBER 1", "WHAT THE\nBRAND SOLD", "the brand sold", color=BLUE),
        *card(710, 330, 500, 380, "NUMBER 2", "WHAT THE\nBUSINESS EARNED", "family business", color=YELLOW),
        *card(1250, 330, 500, 380, "NUMBER 3", "WHAT BELONGS\nTO RYAN", "belongs to Ryan", color=GREEN),
        Stamp("HEADLINES MIX ALL 3", W / 2, 840, at="mix all three", size=70, angle=-3),
    ]))

S.append(Scene("08_keep_board", "01 · The claim", "Keep this board in your head. We're coming back to it.", els=[
    *board([0, 0, 0]),
    Rect(BX - 14, BY - 14, BW + 28, HEAD_H + ROW_H * 3 + 28, fill=(0, 0, 0, 0), outline=YELLOW, width=6,
         shadow=False, at="Keep this board"),
    Text("KEEP THIS IN YOUR HEAD", W / 2, BY + HEAD_H + ROW_H * 3 + 90, size=56, color=YELLOW, at="in your head",
         anim="pop", sfx="pop"),
]))

# 3 BUILDING THE CASE -------------------------------------------------------
S.append(Scene("09_backstory", "02 · The backstory", (
    "Quick backstory. The channel started in 2015 as Ryan ToysReview. It's run by his parents through a family "
    "production company called Sunlight Entertainment, based in Houston, Texas."),
    src="Wikipedia: Ryan's World", els=[
        Rect(200, 470, 1520, 8, fill=LINE, radius=4, shadow=False, grow="right", at=0.2, grow_dur=1.2),
        Text("2015", 380, 400, size=80, color=YELLOW, at="2015"),
        Text("RYAN TOYSREVIEW\nCHANNEL STARTS", 380, 600, size=40, at="as Ryan ToysReview"),
        Text("2019", 960, 400, size=80, color=YELLOW, at=("as Ryan ToysReview", 0.6)),
        Text("RENAMED\nRYAN'S WORLD", 960, 600, size=40, at=("as Ryan ToysReview", 0.8)),
        Text("RUN BY", 1540, 400, size=50, color=MUTED, at="run by his parents"),
        Text("SUNLIGHT\nENTERTAINMENT", 1540, 590, size=44, color=YELLOW, at="Sunlight Entertainment"),
        Text("FAMILY COMPANY · HOUSTON, TX", 1540, 730, size=26, weight="Bold", color=MUTED, at="Houston",
             shadow=False),
    ]))

S.append(Scene("10_forbes", "02 · The backstory", (
    "It grew fast. So fast that Forbes named him the highest-paid YouTuber in the world three years in a row. "
    "Twenty-two million dollars on the 2018 list. Twenty-six million in 2019. Twenty-nine and a half million in "
    "2020. Then twenty-seven million in 2021, when he dropped to seventh."),
    src="Forbes highest-paid YouTubers (via CBS News, Tubefilter)", els=[
        headline("FORBES: HIGHEST-PAID YOUTUBER", y=150, size=64, at=0.1),
        Text("#1 · #1 · #1", W / 2, 235, size=44, color=YELLOW, at="three years in a row", anim="pop", sfx="pop"),
        *[x for i, (yr, v, cue, rank) in enumerate([
            ("2018", 22, "Twenty-two", "#1"), ("2019", 26, "Twenty-six", "#1"),
            ("2020", 29.5, "Twenty-nine", "#1"), ("2021", 27, "twenty-seven", "#7")])
          for x in (
              Rect(330 + i * 340, 900 - v * 18, 220, v * 18, fill=YELLOW if rank == "#1" else (120, 130, 145),
                   grow="up", at=cue, radius=10),
              Counter(440 + i * 340, 900 - v * 18 - 55, v, lambda q, v=v: money(q, 1 if v % 1 else 0), at=cue,
                      size=56, anim="fade"),
              label(yr, 440 + i * 340, 950, at=cue, size=36, color=WHITE),
              label(rank, 440 + i * 340, 870, at=(cue, 0.6), size=34,
                    color=(20, 20, 20) if rank == "#1" else WHITE),
          )],
        Rect(240, 900, 1440, 4, fill=LINE, radius=0, shadow=False, at=0.1),
    ]))

S.append(Scene("11_sum", "02 · The backstory", (
    "Now here's the first clue. Add those up. One hundred and four and a half million dollars. "
    "So that's probably where the hundred million comes from. Case closed?"), glow=YELLOW, els=[
        label("CLUE #1", W / 2, 170, at=0, size=40, color=YELLOW),
        Text("$22M + $26M + $29.5M + $27M", W / 2, 330, size=70, at="Add those up"),
        Rect(560, 410, 800, 6, fill=WHITE, radius=3, shadow=False, grow="right", at=("Add those up", 0.5)),
        Counter(W / 2, 560, 104.5, lambda v: money(v, 1), at="One hundred and four", size=190, color=YELLOW,
                dur=1.4),
        Text("FOUR FORBES LISTS, ADDED TOGETHER", W / 2, 700, size=34, weight="Bold", color=MUTED,
             at="where the hundred million", shadow=False),
        Stamp("CASE CLOSED?", W / 2 + 360, 840, at="Case closed", size=80, color=RED),
    ]))

S.append(Scene("12_forbes_method", "02 · The backstory", (
    "Not quite. Because I read what Forbes actually measures. Those figures are pre-tax. They are before fees to "
    "agents, managers and lawyers. They are estimates built from tracking data and industry interviews, "
    "not audited accounts. And they cover the whole business: ads, sponsorships, licensing and merchandise."),
    src="Forbes methodology (via CBS News)", els=[
        headline("WHAT FORBES ACTUALLY MEASURES", y=170, size=66, at="what Forbes actually measures"),
        *[x for i, (big, small, cue, col) in enumerate([
            ("PRE-TAX", "before any income tax", "pre-tax", RED),
            ("PRE-FEES", "before agents, managers & lawyers", "before fees", RED),
            ("ESTIMATES", "tracking data + interviews, not audited", "estimates", YELLOW),
            ("WHOLE BUSINESS", "ads · sponsors · licensing · merch", "whole business", YELLOW)])
          for x in (
              Rect(260, 280 + i * 165, 1400, 140, at=cue, anim="left"),
              Text("✗" if col == RED else "!", 340, 350 + i * 165, size=70, weight="glyph", color=col, at=cue,
                   anim="pop", sfx="pop"),
              Text(big, 420, 330 + i * 165, size=54, anchor="lm", at=cue, anim="left"),
              Text(small, 420, 385 + i * 165, size=30, weight="SemiBold", color=MUTED, anchor="lm", at=cue,
                   anim="left", shadow=False),
          )],
    ]))

S.append(Scene("13_networth_sites", "02 · The backstory", (
    "Second clue: the \"net worth\" sites. Most articles that say \"a hundred million\" trace back to one estimate "
    "on a celebrity net-worth site. Other trackers put the figure at around twenty to thirty million. "
    "When the same number appears everywhere because everyone copied it, that's not confirmation."),
    src="Celebrity Net Worth; Market Realist", els=[
        label("CLUE #2", W / 2, 140, at=0, size=40, color=YELLOW),
        Shot(shot("cnw.png"), box=(120, 260, 900, 506), at=0.2, anim="left",
             marks=[("ring", "one estimate", (408, 160, 656, 212))]),
        Text("ONE SITE SAYS", 1440, 330, size=36, weight="Bold", color=MUTED, at="one estimate", shadow=False),
        Text("$100M", 1440, 420, size=110, color=RED, at="one estimate"),
        Text("OTHER TRACKERS", 1440, 560, size=36, weight="Bold", color=MUTED, at="Other trackers", shadow=False),
        Text("$20–31M", 1440, 650, size=110, color=GREEN, at="twenty to thirty"),
        Stamp("COPIED ≠ CONFIRMED", W / 2, 900, at="not confirmation", size=74),
    ]))

S.append(Scene("14_ftc", "02 · The backstory", (
    "Third clue: in 2019, a consumer watchdog called Truth in Advertising filed a complaint with the US Federal "
    "Trade Commission about sponsored videos on the channel. The FTC confirmed it received the complaint but "
    "didn't say whether it opened an investigation. That same year, YouTube changed how kids' channels get paid. "
    "And that brings us to my test."), src="truthinadvertising.org; Tubefilter", els=[
        label("CLUE #3", W / 2, 120, at=0, size=40, color=YELLOW, out="That same year"),
        Shot(shot("tina.png"), at=0.1, focus=[("filed a complaint", (60, 215, 850, 560))],
             marks=[("hl", "sponsored videos", (596, 424, 826, 451)),
                    ("hl", ("sponsored videos", 0.5), (72, 458, 802, 486))], out="That same year"),
        Text("A COMPLAINT — NOT A FINDING", W / 2, 940, size=46, color=WHITE, bg=(0, 0, 0, 190), pad=(30, 16),
             at="didn't say", anim="pop", sfx="pop", out="That same year"),
        headline("2019: YOUTUBE CHANGES HOW KIDS' CHANNELS GET PAID", y=H / 2, size=64, at="That same year",
                 anim="pop"),
    ]))

# 4 MY TEST -----------------------------------------------------------------
S.append(Scene("15_test_intro", "03 · My test", (
    "I'm going to take one Forbes year, June 2019 to June 2020, the $29.5 million year, and try to rebuild it from "
    "scratch."), glow=GREEN, els=[
        headline("MY TEST", y=200, size=110, color=GREEN, at=0.1, anim="pop", sfx="hit"),
        Text("JUNE 2019 → JUNE 2020", W / 2, 360, size=56, at="June 2019"),
        Counter(W / 2, 480, 29.5, lambda v: money(v, 1), at="$29.5 million", size=110, color=YELLOW, dur=0.8),
        *card(250, 600, 440, 300, "BUCKET 1", "ADS", "rebuild it", color=BLUE, value_size=70),
        *card(740, 600, 440, 300, "BUCKET 2", "LICENSING", ("rebuild it", 0.3), color=YELLOW, value_size=60),
        *card(1230, 600, 440, 300, "BUCKET 3", "WHAT'S LEFT", ("rebuild it", 0.6), color=GREEN, value_size=56),
    ]))

S.append(Scene("16_ads_coppa", "03 · My test · Bucket 1: ads", (
    "Forbes says the channel got about 12.2 billion views in that period. In 2019, Google and YouTube paid a "
    "$170 million settlement over children's privacy, and YouTube stopped showing personalised ads on videos made "
    "for kids. Kids' content can only show general ads now, and those pay much less. One rights-management firm "
    "reported a kids' channel's revenue falling by more than half even as its views went up."),
    src="Forbes; FTC press release, Sept 2019; Kidscreen", els=[
        Counter(W / 2, 220, 12.2, lambda v: f"{v:.1f} BILLION VIEWS", at="12.2 billion", size=96, dur=1.0),
        label("IN ONE YEAR (FORBES)", W / 2, 310, at="12.2 billion", size=30),
        *card(200, 400, 720, 420, "FTC SETTLEMENT · 2019", "$170M", "$170 million", color=RED, value_size=120,
              value_y=570),
        Text("NO PERSONALISED ADS\nON KIDS' VIDEOS", 560, 730, size=34, weight="Bold", color=WHITE,
             at="stopped showing", shadow=False),
        *card(1000, 400, 720, 420, "ONE KIDS' CHANNEL", "REVENUE −50%+", "falling by more than half",
              color=RED, value_size=76, value_y=570),
        Text("…WHILE VIEWS WENT UP", 1360, 730, size=34, weight="Bold", color=GREEN, at="views went up",
             shadow=False),
    ]))

S.append(Scene("17_ads_calc", "03 · My test · Bucket 1: ads", (
    "So what's a thousand kids' views worth to the creator? Nobody publishes an exact figure, so I'll use a range: "
    "seventy-five cents to two dollars per thousand views. That's my assumption, not a sourced number. "
    "That gives anywhere from about nine million to twenty-four million dollars from ads."), els=[
        headline("WHAT ARE 1,000 KIDS' VIEWS WORTH?", y=170, size=62, at=0.1),
        Text("$0.75 – $2.00", W / 2, 320, size=120, color=YELLOW, at="seventy-five cents", anim="pop"),
        label("PER 1,000 VIEWS", W / 2, 410, at="seventy-five cents", size=32),
        Text("MY ASSUMPTION", 1590, 320, size=34, color=BLUE, bg=(20, 40, 70), pad=(22, 12), outline=BLUE,
             at="my assumption", anim="pop", sfx="pop"),
        Rect(260, 500, 1400, 360, at="That gives"),
        Text("12.2B ÷ 1,000 × $0.75  =", 340, 600, size=52, anchor="lm", at="That gives", anim="left"),
        Counter(1580, 600, 9.2, lambda v: money(v, 1), at="nine million", size=72, color=GREEN, anchor="rm"),
        Text("12.2B ÷ 1,000 × $2.00  =", 340, 760, size=52, anchor="lm", at=("That gives", 0.4), anim="left"),
        Counter(1580, 760, 24.4, lambda v: money(v, 1), at="twenty-four million", size=72, color=GREEN,
                anchor="rm"),
    ]))

S.append(Scene("18_toys", "03 · My test · Bucket 2: licensing", (
    "In 2018, Ryan's World toys launched at Walmart, then reached Target and Amazon. By the end of 2020, there "
    "were around ten thousand licensed products, and the brand was projected to reach half a billion dollars in "
    "retail sales."), src="Tubefilter, Dec 2019 & Dec 2020", els=[
        Text("2018 LAUNCH", W / 2, 160, size=40, weight="Bold", color=MUTED, at=0.1, shadow=False),
        Text("WALMART", 560, 260, size=72, at="Walmart"),
        Text("→ TARGET", 960, 260, size=72, at="Target"),
        Text("→ AMAZON", 1380, 260, size=72, at="Amazon"),
        Counter(560, 470, 10000, lambda v: f"~{v:,.0f}", at="ten thousand", size=120, color=YELLOW),
        label("LICENSED PRODUCTS", 560, 560, at="ten thousand", size=32),
        Counter(1360, 470, 500, lambda v: money(v), at="half a billion", size=120, color=YELLOW),
        label("RETAIL SALES (2020 PROJECTION)", 1360, 560, at="half a billion", size=32),
        Shot(shot("tubefilter_headline.png"), box=(330, 680, 1260, 157), at="half a billion",
             marks=[("hl", ("half a billion", 0.8), (922, 12, 1340, 60))]),
    ]))

S.append(Scene("19_catch", "03 · My test · Bucket 2: licensing", (
    "But here's the catch: half a billion in toy sales is not half a billion for the Kajis."), glow=RED, els=[
        Text("$500M IN TOY SALES", W / 2, 400, size=110, at=0.2),
        Strike(560, 400, 1360, 400, at="is not", width=14),
        Stamp("≠ $500M FOR THE FAMILY", W / 2, 640, at="not half a billion", size=84),
    ]))

FUN_X, FUN_W = 330, 1260
S.append(Scene("20_funnel", "03 · My test · Bucket 2: licensing", (
    "Stores keep their markup. As a rule of thumb, the wholesale price is roughly half of the shelf price, so call "
    "it $250 million. Licensing royalties are paid on wholesale, and for character brands they average about ten "
    "percent. That's about $25 million in royalties, and that has to be shared with pocket.watch, the studio that "
    "manages the brand's licensing."), src="The Licensing Letter (royalty average); Tubefilter", els=[
        headline("FOLLOW THE MONEY", y=130, size=60, at=0),
        Rect(FUN_X, 200, FUN_W, 150, fill=(40, 70, 120), at=0.2, grow="right"),
        Text("$500M  RETAIL", W / 2, 275, size=66, at=0.4),
        Rect(FUN_X + 160, 380, FUN_W - 320, 150, fill=(60, 90, 140), at="roughly half", grow="right"),
        Text("~$250M  WHOLESALE", W / 2, 455, size=60, at="$250 million"),
        label("STORES KEEP\nTHEIR MARKUP", 1460, 455, at="$250 million", size=22, anchor="lm", align="left"),
        Rect(FUN_X + 310, 560, FUN_W - 620, 150, fill=(150, 115, 20), at="ten percent", grow="right"),
        Text("~$25M  ROYALTIES", W / 2, 635, size=52, at="$25 million"),
        label("~10% OF\nWHOLESALE", 1310, 635, at="ten percent", size=22, anchor="lm", align="left"),
        Rect(FUN_X + 370, 740, FUN_W - 740, 150, fill=(30, 110, 70), at="shared with", grow="right"),
        Text("FAMILY + POCKET.WATCH", W / 2, 815, size=36, at="pocket.watch"),
        label("SPLIT NOT PUBLIC", W / 2, 935, at="pocket.watch", size=30, color=YELLOW),
    ]))

S.append(Scene("21_split", "03 · My test · Bucket 2: licensing", (
    "The split between pocket.watch and the family has never been made public. But a Forbes writer said Ryan's "
    "share of the licensing alone made up more than half of his $29.5 million."), src="Forbes, Dec 2020", els=[
        Text("SPLIT: NOT PUBLIC", W / 2, 220, size=72, color=MUTED, at=0.1),
        Rect(260, 430, 1400, 200, fill=(30, 36, 48), at=0.3, radius=16),
        Text("FAMILY  vs  POCKET.WATCH", W / 2, 330, size=40, weight="Bold", color=MUTED, at=0.5, shadow=False,
             out="Forbes writer"),
        Rect(260, 430, 760, 200, fill=YELLOW, at="more than half", grow="right", radius=16),
        Text("LICENSING: MORE THAN HALF", 640, 530, size=40, color=(20, 20, 20), shadow=False,
             at=("more than half", 0.5)),
        Text("$29.5M", 1450, 530, size=64, at="$29.5 million"),
        Text("“more than half” — Forbes", W / 2, 760, size=44, weight="SemiBold", color=WHITE,
             at=("more than half", 0.3)),
    ]))

S.append(Scene("22_match", "03 · My test · Does it match?", (
    "Take \"more than half\" of $29.5 million from licensing. That leaves at most around $14 million for ads and "
    "everything else. That only works if the ad rate was near the bottom of my range, around a dollar per "
    "thousand views. So my rebuild lines up with Forbes, but only if the post-2019 kids' ad cuts hit hard. "
    "Which is exactly what the reporting says happened."), els=[
        headline("DOES MY REBUILD MATCH FORBES?", y=150, size=62, at=0),
        label("ADS + EVERYTHING ELSE: AT MOST", 960, 280, at="at most", size=32),
        Counter(960, 360, 14, lambda v: f"~{money(v)}", at="$14 million", size=96, color=YELLOW, dur=0.8),
        label("MY AD RANGE", 260, 520, at="bottom of my range", size=28, anchor="lm"),
        Rect(260, 560, 1400, 70, fill=(40, 70, 120), at="bottom of my range", grow="right", radius=35),
        label("$9.2M", 260, 670, at="bottom of my range", size=30, anchor="lm", color=WHITE),
        label("$24.4M", 1660, 670, at="bottom of my range", size=30, anchor="rm", color=WHITE),
        Rect(260 + 1400 * (12.2 - 9.2) / 15.2 - 8, 540, 16, 110, fill=YELLOW, radius=8, at="a dollar per",
             anim="pop"),
        Text("≈ $1 PER 1,000 VIEWS → $12.2M", 260 + 1400 * 3 / 15.2, 730, size=40, color=YELLOW,
             at="a dollar per"),
        Stamp("IT MATCHES ✓", W / 2, 900, color=GREEN, at="lines up with Forbes", size=80, angle=-4),
    ]))

WF_BASE, WF_SCALE = 900, 6.0
WF = [("FORBES TOTAL", 104.5, 0, "104.5", (90, 140, 220)), ("− FEES (15%)", 88.8, 104.5, "fees for agents", RED),
      ("− TAX (37%)", 56.0, 88.8, "Then income tax", RED), ("− COSTS", 50.0, 56.0, "staff", RED),
      ("KEPT", 50.0, 0, "fifty million", GREEN)]
S.append(Scene("23_waterfall", "03 · My test · Bucket 3: what's left", (
    "Now let's go from gross to what's actually kept. Start with the $104.5 million from the four Forbes lists. "
    "Take off fees for agents, managers and lawyers. Forbes doesn't. Ten to twenty percent is a common range, so "
    "I'll use fifteen. That's about $89 million. Then income tax. The top US federal rate is thirty-seven percent. "
    "Texas has no state income tax, which helps. After that: roughly $56 million. And that's before paying the "
    "staff, the studio, editing and production. One report describes a team of around thirty people. Even a modest "
    "allowance for that brings the figure to about fifty million dollars, or less."), els=[
        headline("GROSS → KEPT", y=120, size=66, at=0),
        Rect(200, WF_BASE, 1520, 4, fill=LINE, radius=0, shadow=False, at=0),
        *[x for i, (lab, v, prev, cue, col) in enumerate(WF) for x in (
            Rect(260 + i * 300, WF_BASE - max(v, prev) * WF_SCALE, 220, abs(prev - v) * WF_SCALE if prev else v * WF_SCALE,
                 fill=col, grow="up", at=cue, radius=8),
            Text(money(v, 1) if i == 0 else (f"−{money(prev - v, 0)}" if 0 < i < 4 else "~$50M"),
                 370 + i * 300, WF_BASE - max(v, prev) * WF_SCALE - 45, size=48, at=(cue, 0.3),
                 color=WHITE if i in (0, 4) else RED),
            label(lab, 370 + i * 300, WF_BASE + 45, at=cue, size=26, color=WHITE),
        )],
        Text("= $88.8M", 670, WF_BASE - 88.8 * WF_SCALE + 40, size=36, at="$89 million", anim="pop", sfx="pop"),
        Text("= $56.0M", 970, WF_BASE - 56 * WF_SCALE + 40, size=36, at="$56 million", anim="pop", sfx="pop"),
        Text("NO TEXAS STATE INCOME TAX", 1420, 260, size=30, color=BLUE, bg=(20, 40, 70), pad=(20, 10),
             outline=BLUE, at="Texas has no", anim="pop", sfx="pop"),
        label("ESTIMATE · ASSUMPTIONS IN DESCRIPTION", 1720, 1000, at=0.5, size=22, anchor="rm"),
    ]))

# 5 THE REVEAL --------------------------------------------------------------
S.append(Scene("24_reveal", "04 · The reveal", (
    "So here's my number. Over those four Forbes years, the Ryan's World business likely kept somewhere around "
    "forty-five to fifty-five million dollars after fees and tax."), glow=YELLOW, push=0.08, els=[
        label("MY ESTIMATE", W / 2, 300, at="here's my number", size=44, color=MUTED),
        Text("$45M – $55M", W / 2, 520, size=210, color=YELLOW, at="forty-five", anim="pop", sfx="hit"),
        Text("KEPT BY THE BUSINESS · 2018–2021", W / 2, 700, size=46, at="after fees"),
    ]))

S.append(Scene("25_not_ryan", "04 · The reveal", "And that's the business, not Ryan.", els=[
    *card(160, 330, 500, 420, "BRAND SALES", "$500M+\nRETAIL", 0.1, color=BLUE, value_size=66),
    *card(710, 330, 500, 420, "FAMILY BUSINESS", "~$50M\nKEPT", 0.3, color=YELLOW, value_size=66),
    *card(1260, 330, 500, 420, "RYAN", "?", "not Ryan", color=GREEN, value_size=200, outline=GREEN),
    Ring((1300, 380, 1720, 700), at=("not Ryan", 0.3)),
]))

S.append(Scene("26_laws", "04 · Who gets the money", (
    "Who actually owns it? The company is run by his parents. In California, a law called the Coogan Law requires "
    "fifteen percent of a child performer's earnings to go into a protected trust, and since 2025 that covers "
    "child influencers too. Illinois, Utah, Minnesota and several other states have passed similar rules."),
    src="Stateline, Aug 2025; Good Morning America; MultiState", els=[
        headline("WHO ACTUALLY OWNS IT?", y=150, size=70, at=0),
        Text("RUN BY HIS PARENTS", W / 2, 260, size=44, color=MUTED, weight="Bold", at="run by his parents",
             shadow=False),
        *card(160, 340, 760, 420, "CALIFORNIA · COOGAN LAW", "15%\n→ PROTECTED TRUST", "Coogan Law",
              color=GREEN, value_size=72),
        Text("NOW COVERS KID INFLUENCERS (2025)", 540, 820, size=30, color=GREEN, at="child influencers",
             weight="Bold", shadow=False),
        Text("ALSO PASSED SIMILAR LAWS", 1380, 380, size=32, color=MUTED, weight="Bold", at="Illinois",
             shadow=False),
        *[Text(st, 1380, 460 + i * 70, size=50, at=("Illinois", 0.15 * i), anim="right")
          for i, st in enumerate(["ILLINOIS", "UTAH", "MINNESOTA", "ARKANSAS", "MONTANA", "VIRGINIA"])],
    ]))

S.append(Scene("27_texas", "04 · Who gets the money", (
    "But the family is based in Texas. In the state-by-state roundups I found, Texas isn't listed as having a law "
    "like that. So there may be no legal minimum that has to be set aside for Ryan. Some reports say his parents "
    "set up trusts for him and his siblings, but I couldn't find an amount from a reliable source, so I won't guess."),
    src="Stateline, Aug 2025", glow=RED, els=[
        Text("TEXAS", W / 2, 280, size=170, at="based in Texas"),
        Stamp("NOT LISTED", W / 2, 470, at="isn't listed", size=90),
        Text("NO KNOWN LEGAL MINIMUM SET ASIDE FOR RYAN", W / 2, 640, size=46, at="no legal minimum"),
        Text("TRUSTS: REPORTED · AMOUNT: UNKNOWN", W / 2, 800, size=44, color=YELLOW, bg=(0, 0, 0, 170),
             pad=(30, 16), at="set up trusts"),
    ]))

S.append(Scene("28_not_public", "04 · The reveal", (
    "The honest answer is that nobody outside the family knows what Ryan personally has."), push=0.07, els=[
        label("RYAN'S PERSONAL SHARE", W / 2, 400, at=0.1, size=48, color=MUTED),
        Text("NOT PUBLIC", W / 2, 560, size=190, color=WHITE, at="nobody outside", anim="pop", sfx="hit"),
    ]))

S.append(Scene("29_caveats", "04 · Caveats", (
    "Caveats: every number here is an estimate. The Forbes periods don't line up perfectly and leave a gap in 2020, "
    "the years before 2018 and after 2021 aren't counted, and the family runs other channels too. Real lifetime "
    "earnings could be higher. But the gross business total and the personal fortune are still two very different "
    "numbers."), els=[
        headline("CAVEATS", y=160, size=80, color=YELLOW, at=0),
        *[Text("•  " + c, 300, 300 + i * 105, size=46, anchor="lm", at=cue, anim="left", weight="Bold")
          for i, (c, cue) in enumerate([
              ("Every number is an estimate", "every number"),
              ("Forbes periods leave a gap in 2020", "gap in 2020"),
              ("Years before 2018 & after 2021 not counted", "years before 2018"),
              ("The family runs other channels too", "other channels"),
              ("Lifetime earnings could be higher", "could be higher")])],
        Text("GROSS TOTAL ≠ PERSONAL FORTUNE", W / 2, 900, size=58, color=WHITE, bg=(60, 20, 20), pad=(34, 18),
             outline=RED, at="two very different", anim="pop", sfx="pop"),
    ]))

# 6 BACK TO THE BOARD -------------------------------------------------------
S.append(Scene("30_board_return", "05 · Back to the board", (
    "Remember the board? \"Ryan's personal fortune: $100 million.\" The business grossed over $100 million. "
    "After fees and tax, my estimate is about $50 million kept. Ryan's personal share isn't public. "
    "\"Started at 3.\" True. \"Made it from toy videos.\" Mostly from licensing and merchandise, not the videos "
    "themselves."), src="Forbes; my estimate", els=[
        *board([0, 0, 0], found_cues=["The business grossed", "True.", "Mostly from licensing"]),
        Rect(COL_CLAIM - 20, row_y(0) - 70, 480, 140, fill=(0, 0, 0, 0), outline=YELLOW, width=5, shadow=False,
             at="personal fortune", out="The business grossed"),
    ]))

S.append(Scene("31_verdict", "05 · Back to the board", (
    "So did Ryan's World make a hundred million dollars? The brand, almost certainly yes, in gross revenue. "
    "Did Ryan get a hundred million dollars? There's no evidence of that, and the maths says it's very unlikely."),
    els=[
        *board([0, 0, 0], found_cues=[0, 0, 0]),
        Text("✓", BX + BW - 60, row_y(0) - 30, size=60, weight="glyph", color=GREEN, at="almost certainly yes",
             anim="pop", sfx="pop"),
        Strike(COL_CLAIM - 10, row_y(0), COL_CLAIM + 420, row_y(0), at="no evidence"),
        Stamp("RYAN GOT $100M? VERY UNLIKELY", W / 2, BY + HEAD_H + ROW_H * 3 + 95, at="very unlikely", size=56, angle=-3),
    ]))

# 7 FAIR ENDING -------------------------------------------------------------
S.append(Scene("32_fair", "06 · The bigger point", (
    "To be clear, this isn't an attack on Ryan or his family. Ryan is a kid. Building a brand that big is a real "
    "achievement, and nothing here suggests anyone broke the law. My issue is with the number. "
    "\"A hundred million dollars\" turns a family business's gross revenue into a child's bank balance, and those "
    "aren't the same thing."), push=0.03, els=[
        Text("NOT AN ATTACK ON THE FAMILY", W / 2, 240, size=64, at="isn't an attack", out="My issue"),
        Text("A real achievement", W / 2, 400, size=50, weight="SemiBold", color=GREEN, at="real achievement",
             out="My issue"),
        Text("Nothing suggests anyone broke the law", W / 2, 490, size=50, weight="SemiBold", color=GREEN,
             at="broke the law", out="My issue"),
        headline("MY ISSUE IS THE NUMBER", y=300, size=80, color=YELLOW, at="My issue"),
        *card(260, 460, 620, 340, "WHAT IT IS", "FAMILY BUSINESS\nGROSS REVENUE", "turns a family", color=WHITE,
              value_size=46),
        Text("→", W / 2, 630, size=110, color=RED, at="into a child's"),
        *card(1040, 460, 620, 340, "WHAT HEADLINES SAY", "A CHILD'S\nBANK BALANCE", "into a child's", color=RED,
              value_size=46),
    ]))

S.append(Scene("33_bigger", "06 · The bigger point", (
    "And there's a bigger question: when a child is the face of the business, who protects their share? More states "
    "are starting to write laws for exactly this. That's probably the most important thing in this whole story."),
    src="Stateline, Aug 2025", push=0.06, els=[
        Text("WHO PROTECTS", W / 2, 400, size=120, at="who protects"),
        Text("THE CHILD'S SHARE?", W / 2, 540, size=120, color=YELLOW, at=("who protects", 0.3)),
        Text("MORE STATES ARE WRITING LAWS FOR THIS", W / 2, 740, size=44, color=GREEN, at="More states",
             weight="Bold", shadow=False),
    ]))

S.append(Scene("34_pick", "07 · My final pick", (
    "My final pick: Ryan's World grossed more than $100 million. The business kept about half of that. And Ryan's "
    "own share is something only his family knows."), glow=GREEN, els=[
        headline("MY FINAL PICK", y=180, size=90, color=GREEN, at=0, anim="pop", sfx="hit"),
        Rect(260, 300, 1400, 520, at=0.2),
        *[x for i, (k_, v_, cue, col) in enumerate([
            ("GROSSED", "$100M+", "grossed more", BLUE), ("BUSINESS KEPT", "~$50M", "kept about half", YELLOW),
            ("RYAN'S SHARE", "ONLY HIS FAMILY KNOWS", "only his family", GREEN)])
          for x in (
              label(k_, 330, 390 + i * 160, at=cue, size=32, anchor="lm"),
              Text(v_, 1590, 390 + i * 160, size=70 if i < 2 else 54, color=col, anchor="rm", at=cue, anim="right"),
          )],
    ]))

S.append(Scene("35_cta", "", (
    "What's your guess? How much do you think Ryan actually has? Comment below. And if you want to see what happened "
    "to other child YouTubers' money, that's the next video."), els=[
        Text("WHAT'S YOUR GUESS?", W / 2, 300, size=110, color=YELLOW, at=0.1, anim="pop", sfx="hit"),
        Text("$ ____ M", W / 2, 480, size=130, at="How much"),
        Text("COMMENT BELOW ↓", W / 2, 640, size=58, at="Comment below", bg=(150, 20, 20), pad=(40, 20),
             anim="pop", sfx="pop"),
        Text("NEXT: WHAT HAPPENED TO OTHER CHILD YOUTUBERS' MONEY?", W / 2, 860, size=40, color=MUTED,
             weight="Bold", at="next video", shadow=False),
    ]))

S.append(Scene("36_endscreen", "", "", hold=12, push=0.0, els=[
    Rect(140, 300, 760, 428, fill=(0, 0, 0, 0), outline=(70, 78, 92), width=3, shadow=False, at=0),
    label("END-SCREEN VIDEO SLOT", 520, 514, at=0, size=28),
    Rect(1020, 300, 760, 428, fill=(0, 0, 0, 0), outline=(70, 78, 92), width=3, shadow=False, at=0),
    label("END-SCREEN VIDEO SLOT", 1400, 514, at=0, size=28),
    Text("THANKS FOR WATCHING", W / 2, 180, size=64, at=0.2),
    Text("Sources & assumptions in the description", W / 2, 860, size=36, weight="SemiBold", color=MUTED, at=0.5,
         shadow=False),
]))

SCENES = S
