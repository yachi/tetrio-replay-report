import RouteOrders.T1
import RouteOrders.T1Witness
import RouteOrders.Hold
import RouteOrders.NodeData
import RouteOrders.HoldMutants
import RouteOrders.HoldWitness
import RouteOrders.Generated.SdpcspinCounts
import RouteOrders.Discriminate


/-! The Lean half of the route-order proofs (`pipeline/sim/route-orders.ts`).

* `RouteOrders.T1Defs` / `RouteOrders.HoldDefs` — the models only (no theorem), which is where
                            `mutate.sh` plants its mutants, so the witnesses still build under them
* `RouteOrders.T1`        — T1, order independence of the sequential engine clear, and the
                            `indexOf` write process equal to the model's (`placeAllIdx_eq_placeAll`)
* `RouteOrders.T1Witness` — each T1 mutant clear is order-dependent on a concrete board (decide)
* `RouteOrders.Hold`      — T2 (procedure ⇔ step relation) and T4 (empty hold ≡ next held)
* `RouteOrders.HoldWitness` — each T2 specification mutant disagrees with the real `acc`, and the
                            procedure without case (c) splits T4's two modes, on a toy DAG (decide)
* `RouteOrders.Generated` — T3, the artefact's counts and bitsets recomputed (native_decide);
                            generated at check time by `gen_data.py`, never committed
* `RouteOrders.Discriminate` — the T2/T4 mutants on the committed data: each changes a count, except
                            `starWild`, which is proved equivalent there
-/
