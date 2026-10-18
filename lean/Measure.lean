import RouteOrders.HoldMutants
import RouteOrders.Generated.SdpcspinData
open RouteOrders.NodeData RouteOrders.Generated RouteOrders.HoldMutants

def main : IO Unit := do
  IO.println "node\tartefact(empty/next)\treal(empty/next)\tnoHoldFirst(empty/next)\tstarWild(empty/next)\tholdOnly(empty/next)"
  for n in nodes do
    let f (m : Mut) := s!"{countMutEmpty m n}/{countMutNext m n}"
    IO.println s!"{n.name}\t{n.artEmpty}/{n.artNext}\t{f {}}\t{f {noHoldFirst := true}}\t{f {starWild := true}}\t{f {holdOnly := true}}"
