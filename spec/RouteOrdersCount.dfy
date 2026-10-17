// RouteOrdersCount.dfy — T3, the counts, computed by the PROVED procedure.
//
// For every node of a route-orders artefact, run `AcceptsMemo` (RouteOrders.dfy: proved equal to
// `Accepts`, which AccIffReach proves decides the hold relation `Reach`) over all 5040 dealt
// orders, from an empty hold ("empty") and from the first piece already held ("next"), and print
// the accepted count and the accepted bitset in the artefact's own encoding (bit j = order j of
// route-orders.ts `allOrders()`, LSB first within each byte, hex).
//
// It reads nothing at run time. The DAGs come from module RouteOrdersData, which
// spec/route_orders_data.py GENERATES from the artefact into a scratch directory at check time
// (never a committed second copy) and passes with `--input`:
//
//   python3 spec/route_orders_data.py analysis/sdpcspin-orders.json --check     # counts + bitsets
//   python3 spec/route_orders_data.py analysis/sdpcspin-orders.json --mutants   # each T2 mutant moves a count
//
// argv[1] names the mutant switched on (`none` for the proved procedure). The DAG edges are data:
// nothing here checks that an edge is buildable, only what the hold rules make of the edges.
include "RouteOrders.dfy"

module RouteOrdersCount {
  import opened RouteOrders
  import RouteOrdersData

  const PIECES: seq<char> := "IOTSZJL"

  // route-orders.ts allOrders(): rec(pre, left) pushes pre at the leaf and recurses on each
  // left[i] in index order, so the list is lexicographic in the index of each piece in PIECES
  function Perms(pre: seq<char>, left: seq<char>): seq<seq<char>>
    decreases |left|, 1
  {
    if |left| == 0 then [pre] else PermsFrom(pre, left, 0)
  }

  function PermsFrom(pre: seq<char>, left: seq<char>, i: nat): seq<seq<char>>
    requires |left| > 0
    decreases |left|, 0, |left| - i
  {
    if i >= |left| then []
    else Perms(pre + [left[i]], left[..i] + left[i + 1..]) + PermsFrom(pre, left, i + 1)
  }

  function MutOf(name: string): Mut
  {
    if name == "noSwap" then Mut(true, false, false, false, false)
    else if name == "noHoldFirst" then Mut(false, true, false, false, false)
    else if name == "placeStar" then Mut(false, false, true, false, false)
    else if name == "noStar" then Mut(false, false, false, true, false)
    else if name == "holdNoPlace" then Mut(false, false, false, false, true)
    else NoMut
  }

  function HexDigit(v: nat): char
    requires v < 16
  {
    "0123456789abcdef"[v]
  }

  // byte b = bits 8b .. 8b+7, bit 8b+j weighted 2^j (bitsHex: LSB first within each byte)
  method Hex(bits: seq<bool>) returns (out: string)
  {
    out := "";
    var b := 0;
    while b * 8 < |bits|
      decreases |bits| - b * 8
    {
      var v := 0;
      var j := 7;
      while j >= 0
        decreases j + 1
        invariant 0 <= v < 256
        invariant -1 <= j <= 7
        invariant v < Pow2(7 - j)
      {
        v := 2 * v + (if b * 8 + j < |bits| && bits[b * 8 + j] then 1 else 0);
        j := j - 1;
      }
      out := out + [HexDigit(v / 16), HexDigit(v % 16)];
      b := b + 1;
    }
  }

  method Main(args: seq<string>)
  {
    var name := if |args| > 1 then args[1] else "none";
    var m := MutOf(name);
    var orders := Perms([], PIECES);
    print "mutant ", name, " orders ", |orders|, "\n";
    var nodes := RouteOrdersData.NODES;
    var n := 0;
    while n < |nodes|
    {
      var nd := nodes[n];
      var bitsE: seq<bool> := [];
      var bitsN: seq<bool> := [];
      var cE := 0;
      var cN := 0;
      var j := 0;
      while j < |orders|
      {
        var q := orders[j];
        var a := AcceptsMemo(nd.1, m, q, Empty);
        var b := false;
        if |q| > 0 { b := AcceptsMemo(nd.1, m, q[1..], Held(q[0])); }
        bitsE := bitsE + [a];
        bitsN := bitsN + [b];
        if a { cE := cE + 1; }
        if b { cN := cN + 1; }
        j := j + 1;
      }
      var hE := Hex(bitsE);
      var hN := Hex(bitsN);
      print "node ", nd.0, " empty ", cE, " next ", cN, " ", hE, " ", hN, "\n";
      n := n + 1;
    }
  }
}
