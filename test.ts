// Compile-only asset resolution test. This file is not imported with the asset pack.
const collectibleImageSmokeTest: Image[] = [
    assets.image`Coin`,
    assets.image`Energy Orb`,
    assets.image`Crystal`,
    assets.image`Star`,
    assets.image`Heart`,
    assets.image`Key`,
    assets.image`Potion`,
    assets.image`Berries`,
    assets.image`Gear`,
    assets.image`Energy Cell`,
    assets.image`Crown`,
    assets.image`Wrapped Candy`,
]

const collectibleAnimationSmokeTest: Image[][] = [
    assets.animation`Spinning Coin - Idle`,
    assets.animation`Spinning Coin - Collected`,
    assets.animation`Orbiting Energy Orb - Idle`,
    assets.animation`Orbiting Energy Orb - Collected`,
    assets.animation`Shimmering Crystal - Idle`,
    assets.animation`Shimmering Crystal - Collected`,
    assets.animation`Pulsing Star - Idle`,
    assets.animation`Pulsing Star - Collected`,
    assets.animation`Orbiting Heart - Idle`,
    assets.animation`Orbiting Heart - Collected`,
    assets.animation`Swaying Key - Idle`,
    assets.animation`Swaying Key - Collected`,
    assets.animation`Bubbling Potion - Idle`,
    assets.animation`Bubbling Potion - Collected`,
    assets.animation`Swinging Berries - Idle`,
    assets.animation`Swinging Berries - Collected`,
    assets.animation`Turning Gear - Idle`,
    assets.animation`Turning Gear - Collected`,
    assets.animation`Pulsing Energy Cell - Idle`,
    assets.animation`Pulsing Energy Cell - Collected`,
    assets.animation`Gliding Crown - Idle`,
    assets.animation`Gliding Crown - Collected`,
    assets.animation`Wrapped Candy - Idle`,
    assets.animation`Wrapped Candy - Collected`,
];

if (collectibleImageSmokeTest.length != 12) {
    control.panic(12)
}

if (collectibleAnimationSmokeTest.length != 24) {
    control.panic(24)
}
