from collections import namedtuple
import secrets
import numpy as np



PrivateKey = namedtuple("PrivateKey", ["lam", "mu"])
PublicKey = namedtuple("PublicKey", ["g", "n", "n_squared"])

class Paillier:
    TEST_BIT_LENGTH = 32

    def __init__(self, bit_length: int = TEST_BIT_LENGTH):
        self.bit_length = bit_length
        self.private_key, self.public_key = (427917030, 988965434), (63377746067892575, 
                                                                     2567604913,
                                                                     6592594989261737569)


    @staticmethod
    def generate_primes(n: int) -> np.ndarray:
   # https://stackoverflow.com/questions/2068372/fastest-way-to-list-all-primes-below-n-in-python/3035188#3035188
        sieve = np.ones(n // 3 + (n % 6 == 2), dtype=bool)
        for i in range(1, int(n ** 0.5) // 3 + 1):
            if sieve[i]:
                k = 3 * i + 1 | 1
                sieve[k * k // 3 :: 2 * k] = False
                sieve[k * (k - 2 * (i & 1) + 4) // 3 :: 2 * k] = False
        return np.r_[2, 3, ((3 * np.nonzero(sieve)[0][1:] + 1) | 1)]

    @staticmethod
    def L(n: int, x: int) -> int:
        return (x - 1) // n

    def create_key_pair(self) -> tuple[PrivateKey, PublicKey]:
        primes = self.generate_primes(2 ** (self.bit_length // 2)).tolist()

        p = secrets.choice(primes)
        q = secrets.choice(primes)
        n = p * q

        # Convert n to a native Python integer
        n = int(n)

        while p == q or n.bit_length() != self.bit_length or np.gcd(n, (p - 1) * (q - 1)) != 1:
            p = secrets.choice(primes)
            q = secrets.choice(primes)
            n = int(p * q)  # Convert to native Python int here as well

        n_squared = n ** 2
        g = secrets.randbelow(n_squared - 1) + 1
        public_key = PublicKey(g, n, n_squared)

        lam = int(np.lcm(p - 1, q - 1))

        try:
            mu = pow(self.L(n, pow(g, lam, n_squared)), -1, n)
        except ValueError:
            # If an error occurs, recursively call create_key_pair until it succeeds
            return self.create_key_pair()

        private_key = PrivateKey(lam, mu)
        print("privat k",private_key)
        print(public_key)
        return private_key, public_key

    def encrypt(self, plaintext: int) -> int:
        g, n, n_squared = self.public_key
        r = secrets.randbelow(n)
        return (pow(g, plaintext, n_squared) * pow(r, n, n_squared)) % n_squared

    def decrypt(self, ciphertext: int) -> int:
        lam, mu = self.private_key
        _, n, n_squared = self.public_key
        return (self.L(n, pow(ciphertext, lam, n_squared)) * mu) % n

    def add(self, ciphertext_a: int, ciphertext_b: int) -> int:
        _, _, n_squared = self.public_key
        return (ciphertext_a * ciphertext_b) % n_squared

    def test_encrypt_and_decrypt(self, plaintext: int):
        ciphertext = self.encrypt(plaintext)
        print("Ciphertext:", ciphertext)
        assert ciphertext != plaintext

        decrypted = self.decrypt(ciphertext)
        print("Decrypted:", decrypted)
        assert decrypted == plaintext

paillier = Paillier()

decryptTot = paillier.decrypt(3353763009409738967+5493004157871483702)
print(decryptTot)
