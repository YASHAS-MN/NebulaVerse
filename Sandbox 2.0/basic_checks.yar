rule Suspicious_Strings {
    meta:
        description = "Detects strings common in credential stealers"
    strings:
        $s1 = "Login Data" ascii wide        // Browser login file
        $s2 = "Web Data" ascii wide          // Browser payment file
        $s3 = "cookies.sqlite" ascii wide    // Browser cookies
    condition:
        any of them
}
rule EICAR_Test_Pattern {
    strings:
        $eicar = "EICAR-STANDARD-ANTIVIRUS-TEST-FILE"
    condition:
        $eicar
}
