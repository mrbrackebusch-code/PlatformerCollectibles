// Compile-only asset resolution test.
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

const collectiblePublicImageSmokeTest: Image[] = [
    Platformer_Animated_Collectibles.Coin,
    Platformer_Animated_Collectibles.Energy_Orb,
    Platformer_Animated_Collectibles.Crystal,
    Platformer_Animated_Collectibles.Star,
    Platformer_Animated_Collectibles.Heart,
    Platformer_Animated_Collectibles.Key,
    Platformer_Animated_Collectibles.Potion,
    Platformer_Animated_Collectibles.Berries,
    Platformer_Animated_Collectibles.Gear,
    Platformer_Animated_Collectibles.Energy_Cell,
    Platformer_Animated_Collectibles.Crown,
    Platformer_Animated_Collectibles.Wrapped_Candy,
]

const collectiblePublicAnimationSmokeTest: Image[][] = [
    Platformer_Animated_Collectibles.Spinning_Coin__Idle,
    Platformer_Animated_Collectibles.Spinning_Coin__Collected,
    Platformer_Animated_Collectibles.Orbiting_Energy_Orb__Idle,
    Platformer_Animated_Collectibles.Orbiting_Energy_Orb__Collected,
    Platformer_Animated_Collectibles.Shimmering_Crystal__Idle,
    Platformer_Animated_Collectibles.Shimmering_Crystal__Collected,
    Platformer_Animated_Collectibles.Pulsing_Star__Idle,
    Platformer_Animated_Collectibles.Pulsing_Star__Collected,
    Platformer_Animated_Collectibles.Orbiting_Heart__Idle,
    Platformer_Animated_Collectibles.Orbiting_Heart__Collected,
    Platformer_Animated_Collectibles.Swaying_Key__Idle,
    Platformer_Animated_Collectibles.Swaying_Key__Collected,
    Platformer_Animated_Collectibles.Bubbling_Potion__Idle,
    Platformer_Animated_Collectibles.Bubbling_Potion__Collected,
    Platformer_Animated_Collectibles.Swinging_Berries__Idle,
    Platformer_Animated_Collectibles.Swinging_Berries__Collected,
    Platformer_Animated_Collectibles.Turning_Gear__Idle,
    Platformer_Animated_Collectibles.Turning_Gear__Collected,
    Platformer_Animated_Collectibles.Pulsing_Energy_Cell__Idle,
    Platformer_Animated_Collectibles.Pulsing_Energy_Cell__Collected,
    Platformer_Animated_Collectibles.Gliding_Crown__Idle,
    Platformer_Animated_Collectibles.Gliding_Crown__Collected,
    Platformer_Animated_Collectibles.Wrapped_Candy__Idle,
    Platformer_Animated_Collectibles.Wrapped_Candy__Collected,
];

if (collectibleImageSmokeTest.length != 12 || collectiblePublicImageSmokeTest.length != 12) {
    control.panic(12)
}

if (collectibleAnimationSmokeTest.length != 24 || collectiblePublicAnimationSmokeTest.length != 24) {
    control.panic(24)
}
