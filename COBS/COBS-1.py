from cobs import cobs

def test(original):
    encoded = cobs.encode(original)
    decoded = cobs.decode(encoded)
    print("encoded =", encoded)
    print("decoded =", decoded)
    print("original=", original)

    if decoded == original:
        print("Pass")
    else:
        print("Fail")


test(b'Hello world\x00This is a test')
test(b'\x00'*25)

