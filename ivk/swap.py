def swap_bytes(bytes, freq):
    if freq > (len(bytes)//2):
        return
    i = 0
    while i < (len(bytes)-1.5*freq):
        for j in range(freq):
            bytes[i+freq+j] = bytes[i+j] ^ bytes[i+freq+j]
            bytes[i+j] = bytes[i+j] ^ bytes[i+freq+j]
            bytes[i+freq+j] = bytes[i + j] ^ bytes[i + freq + j]
        i += 2 * freq