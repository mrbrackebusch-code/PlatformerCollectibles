// Compile-only asset resolution test. This file is not imported with the asset pack.
const collectibleAnimationSmokeTest: Image[][] = [
    assets.animation`Spinning Coin - Idle`,
    assets.animation`Spinning Coin - Collected`,
    assets.animation`Bobbing Energy Orb - Idle`,
    assets.animation`Bobbing Energy Orb - Collected`,
    assets.animation`Shimmering Crystal - Idle`,
    assets.animation`Shimmering Crystal - Collected`,
    assets.animation`Pulsing Star - Idle`,
    assets.animation`Pulsing Star - Collected`,
    assets.animation`Beating Heart - Idle`,
    assets.animation`Beating Heart - Collected`,
    assets.animation`Glinting Key - Idle`,
    assets.animation`Glinting Key - Collected`,
    assets.animation`Bubbling Potion - Idle`,
    assets.animation`Bubbling Potion - Collected`,
    assets.animation`Bouncing Berries - Idle`,
    assets.animation`Bouncing Berries - Collected`,
    assets.animation`Turning Gear - Idle`,
    assets.animation`Turning Gear - Collected`,
    assets.animation`Pulsing Energy Cell - Idle`,
    assets.animation`Pulsing Energy Cell - Collected`,
    assets.animation`Floating Crown - Idle`,
    assets.animation`Floating Crown - Collected`,
    assets.animation`Drifting Feather - Idle`,
    assets.animation`Drifting Feather - Collected`,
];

if (collectibleAnimationSmokeTest.length != 24) {
    control.panic(24)
}
