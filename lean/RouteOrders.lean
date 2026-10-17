import RouteOrders.T1
import RouteOrders.T1Witness
import RouteOrders.Hold
import RouteOrders.NodeData
import RouteOrders.HoldMutants
import RouteOrders.Generated.SdpcspinCounts
import RouteOrders.Discriminate


/-! The Lean half of the route-order proofs (`pipeline/sim/route-orders.ts`).

* `RouteOrders.T1`        — T1, order independence of the sequential engine clear (+ witnesses)
* `RouteOrders.Hold`      — T2 (procedure ⇔ step relation) and T4 (empty hold ≡ next held)
* `RouteOrders.Generated` — T3, the artefact's counts and bitsets recomputed (native_decide);
                            generated at check time by `gen_data.py`, never committed
* `RouteOrders.Discriminate` — the T2/T4 mutants on the committed data: each changes a count, except
                            `starWild`, which is proved equivalent there
-/
