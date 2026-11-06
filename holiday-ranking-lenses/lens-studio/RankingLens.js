// RankingLens.js  —  "Rank 1-10" Snapchat lens logic (Lens Studio 5.x, JavaScript)
//
// How it plays:
//   1. A card above your head shuffles through random pictures, then stops on one.
//   2. Tap a number (1-10) on the left: that card's picture is placed on that number.
//   3. The head card shuffles again and lands on a new picture (never a repeat).
//   4. After all 10 numbers are filled, the head card hides. Tap again to start over.
//
// Setup is in README.md. In short:
//   - Head Card  : an Image on a Head Binding (follows your head).
//   - Number Strip: a Screen Image showing number-strip.png, on the left of the screen.
//   - Cards      : drag ALL of one category's .jpg files into the "Cards" list.
//
//@input Asset.Texture[] cards {"label":"Cards (drag all images here)"}
//@input Component.Image headCard {"label":"Head Card Image"}
//@input Component.Image numberStrip {"label":"Number Strip (Screen Image)"}
//@input int slotCount = 10 {"label":"How Many Numbers"}
//@input float shuffleTime = 1.2 {"label":"Shuffle Time (sec)"}
//@input float flipEvery = 0.07 {"label":"Flip Speed (sec)"}
//@input float slotInset = 0.06 {"label":"Picture Padding In Box"}
//@input Component.AudioComponent tickSound {"label":"Tick Sound (optional)"}
//@input Component.AudioComponent placeSound {"label":"Place Sound (optional)"}

var N = script.slotCount;
var stripST = script.numberStrip.getSceneObject().getComponent("Component.ScreenTransform");

var slotImages = [];   // Image component per number
var filled = [];       // bool per number
var deck = [];         // remaining card indices (shuffled)
var current = -1;      // card index currently on the head
var shuffling = false;
var finished = false;
var timeLeft = 0;
var flipTimer = 0;

// ---------- build the 10 picture slots on top of the number strip ----------
function buildSlots() {
    var parent = script.numberStrip.getSceneObject();
    for (var i = 0; i < N; i++) {
        var obj = global.scene.createSceneObject("Slot " + (i + 1));
        obj.setParent(parent);
        var st = obj.createComponent("Component.ScreenTransform");
        // strip local space: x,y in [-1, 1], y = +1 is the top (number 1)
        var cellH = 2 / N;
        var top = 1 - i * cellH;
        var bottom = top - cellH;
        var pad = script.slotInset * 2;
        st.anchors = Rect.create(-1 + pad, 1 - pad, bottom + pad * 0.5, top - pad * 0.5);
        st.offsets = Rect.create(0, 0, 0, 0);

        var img = obj.createComponent("Component.Image");
        img.mainMaterial = script.headCard.mainMaterial.clone();
        img.stretchMode = StretchMode.Fit;
        obj.enabled = false;
        slotImages.push(img);
    }
}

function shuffleDeck() {
    deck = [];
    for (var i = 0; i < script.cards.length; i++) deck.push(i);
    for (var j = deck.length - 1; j > 0; j--) {
        var k = Math.floor(Math.random() * (j + 1));
        var t = deck[j]; deck[j] = deck[k]; deck[k] = t;
    }
}

function showOnHead(index) {
    script.headCard.mainPass.baseTex = script.cards[index];
}

function startShuffle() {
    if (deck.length === 0) { finish(); return; }
    shuffling = true;
    timeLeft = script.shuffleTime;
    flipTimer = 0;
    script.headCard.getSceneObject().enabled = true;
}

function finish() {
    finished = true;
    shuffling = false;
    current = -1;
    script.headCard.getSceneObject().enabled = false;
}

function resetGame() {
    finished = false;
    for (var i = 0; i < N; i++) {
        filled[i] = false;
        slotImages[i].getSceneObject().enabled = false;
    }
    shuffleDeck();
    startShuffle();
}

function play(audio) {
    if (audio) { try { audio.play(1); } catch (e) {} }
}

// ---------- per-frame shuffle animation ----------
script.createEvent("UpdateEvent").bind(function () {
    if (!shuffling) return;
    var dt = getDeltaTime();
    timeLeft -= dt;
    flipTimer -= dt;
    if (timeLeft <= 0) {
        shuffling = false;
        current = deck.pop();          // the card you have to rank
        showOnHead(current);
        return;
    }
    if (flipTimer <= 0) {
        flipTimer = script.flipEvery;
        showOnHead(Math.floor(Math.random() * script.cards.length));
        play(script.tickSound);
    }
});

// ---------- tap a number ----------
function slotAt(screenPos) {
    if (!stripST.containsScreenPoint(screenPos)) return -1;
    var local = stripST.screenPointToLocalPoint(screenPos); // -1..1, +1 = top
    var row = Math.floor((1 - local.y) / 2 * N);
    return Math.max(0, Math.min(N - 1, row));
}

script.createEvent("TapEvent").bind(function (e) {
    if (finished) { resetGame(); return; }
    if (shuffling || current < 0) return;
    var slot = slotAt(e.getTapPosition());
    if (slot < 0 || filled[slot]) return;

    filled[slot] = true;
    slotImages[slot].mainPass.baseTex = script.cards[current];
    slotImages[slot].getSceneObject().enabled = true;
    current = -1;
    play(script.placeSound);

    var allFilled = true;
    for (var i = 0; i < N; i++) if (!filled[i]) allFilled = false;
    if (allFilled) finish(); else startShuffle();
});

// ---------- start ----------
if (!script.cards || script.cards.length === 0) {
    print("RankingLens: drag your card images into the Cards list!");
} else {
    // let taps reach the lens, but keep Snapchat's double-tap camera flip
    try {
        global.touchSystem.touchBlocking = true;
        global.touchSystem.enableTouchBlockingException("TouchTypeDoubleTap", true);
    } catch (err) {}
    buildSlots();
    resetGame();
}
