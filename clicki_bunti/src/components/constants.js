export const CAP_WARM = "w";
export const CAP_COLD = "c";
export const CAP_R = "r";
export const CAP_G = "g";
export const CAP_B = "b";
export const CAP_ALL = 'all';
export const ALL_CAPS = [CAP_WARM, CAP_COLD, CAP_R, CAP_G, CAP_B];

export const CAPABILITIES = {
    "/haspa/licht/1": ["w", "c"],
    "/haspa/licht/2": ["w", "c"],
    "/haspa/licht/3": ["w", "c"],
    "/haspa/licht/4": ["w", "c"],
    "/haspa/tisch/1/vorne": ["w", "r", "g", "b"],
    "/haspa/tisch/1/hinten": ["w", "r", "g", "b"],
    "/haspa/tisch/2/vorne": ["w", "r", "g", "b"],
    "/haspa/tisch/2/hinten": ["w", "r", "g", "b"],
    "/haspa/terrasse/1": ["w", "r", "g", "b"],
    "/haspa/terrasse/2": ["w", "r", "g", "b"],
    "/haspa/terrasse/3": ["w", "r", "g", "b"],
    "/haspa/terrasse/4": ["w", "r", "g", "b"],
}

export const MAPPINGS = {
    "/haspa/licht": ["/haspa/licht/1", "/haspa/licht/2", "/haspa/licht/3", "/haspa/licht/4"],
    "/haspa/terrasse": ["/haspa/terrasse/1", "/haspa/terrasse/2", "/haspa/terrasse/3", "/haspa/terrasse/4"],
    "/haspa/tisch/1": ["/haspa/tisch/1/vorne", "/haspa/tisch/1/hinten"],
    "/haspa/tisch/2": ["/haspa/tisch/2/vorne", "/haspa/tisch/2/hinten"],
}
