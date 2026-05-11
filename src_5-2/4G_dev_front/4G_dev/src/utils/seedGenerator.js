export function seededRandom(seed) {
    let hash = 0
    for (let i = 0; i < seed.length; i++) {
        const char = seed.charCodeAt(i)
        hash = ((hash << 5) - hash) + char
        hash = hash & hash
    }
    let state = Math.abs(hash) || 1
    return function () {
        state = (state * 1664525 + 1013904223) & 0xffffffff
        return (state >>> 0) / 0xffffffff
    }
}

export function randInt(rng, min, max) {
    return Math.floor(rng() * (max - min + 1)) + min
}

export function randChoice(rng, arr) {
    const index = Math.floor(rng() * arr.length)
    return arr[index]
}

export function generateFromSeed(seedStr, count) {
    const rng = seededRandom(seedStr)
    const dataTypes = ['0', '1', '2', '3', '4', '5']
    const modbusTypes = ['0', '4']
    const result = []
    for (let i = 0; i < count; i++) {
        result.push({
            varName: `var_${seedStr}_${i}`,
            dataType: randChoice(rng, dataTypes),
            modbusType: randChoice(rng, modbusTypes),
            modbusAddr: randInt(rng, 0, 100),
            data_len: randInt(rng, 1, 8)
        })
    }
    return result
}
