//! A minimal JSON reader (integers only), enough for the sets crate's output. No dependencies.
#[derive(Debug, Clone)]
#[allow(dead_code)]
pub enum J { Null, Bool(bool), Num(i64), Str(String), Arr(Vec<J>), Obj(Vec<(String, J)>) }

impl J {
    pub fn get(&self, k: &str) -> &J {
        match self {
            J::Obj(v) => v.iter().find(|(a, _)| a == k).map(|(_, b)| b).unwrap_or_else(|| panic!("missing key {}", k)),
            _ => panic!("not an object: {}", k),
        }
    }
    pub fn arr(&self) -> &[J] { match self { J::Arr(v) => v, _ => panic!("not an array") } }
    pub fn int(&self) -> i64 { match self { J::Num(n) => *n, _ => panic!("not a number") } }
    pub fn us(&self) -> usize { self.int() as usize }
    pub fn str(&self) -> &str { match self { J::Str(s) => s, _ => panic!("not a string") } }
    pub fn us_list(&self) -> Vec<usize> { self.arr().iter().map(|x| x.us()).collect() }
    pub fn is_leaf(&self) -> bool { matches!(self, J::Obj(v) if v.iter().any(|(a, _)| a == "m")) }
}

pub fn parse(s: &str) -> J {
    let b = s.as_bytes();
    let mut i = 0;
    let v = val(b, &mut i);
    ws(b, &mut i);
    assert!(i == b.len(), "trailing json");
    v
}
fn ws(b: &[u8], i: &mut usize) { while *i < b.len() && (b[*i] as char).is_ascii_whitespace() { *i += 1; } }
fn val(b: &[u8], i: &mut usize) -> J {
    ws(b, i);
    match b[*i] {
        b'{' => {
            *i += 1; let mut v = vec![];
            ws(b, i);
            if b[*i] == b'}' { *i += 1; return J::Obj(v); }
            loop {
                ws(b, i); let k = match val(b, i) { J::Str(s) => s, _ => panic!("key") };
                ws(b, i); assert!(b[*i] == b':'); *i += 1;
                v.push((k, val(b, i))); ws(b, i);
                if b[*i] == b',' { *i += 1; } else { assert!(b[*i] == b'}'); *i += 1; return J::Obj(v); }
            }
        }
        b'[' => {
            *i += 1; let mut v = vec![];
            ws(b, i);
            if b[*i] == b']' { *i += 1; return J::Arr(v); }
            loop {
                v.push(val(b, i)); ws(b, i);
                if b[*i] == b',' { *i += 1; } else { assert!(b[*i] == b']'); *i += 1; return J::Arr(v); }
            }
        }
        b'"' => {
            *i += 1; let st = *i;
            while b[*i] != b'"' { assert!(b[*i] != b'\\', "escapes unsupported"); *i += 1; }
            let s = std::str::from_utf8(&b[st..*i]).unwrap().to_string(); *i += 1; J::Str(s)
        }
        b't' => { *i += 4; J::Bool(true) }
        b'f' => { *i += 5; J::Bool(false) }
        b'n' => { *i += 4; J::Null }
        _ => {
            let st = *i; if b[*i] == b'-' { *i += 1; }
            while *i < b.len() && b[*i].is_ascii_digit() { *i += 1; }
            J::Num(std::str::from_utf8(&b[st..*i]).unwrap().parse().expect("integer"))
        }
    }
}
