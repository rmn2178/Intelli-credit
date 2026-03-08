"""
Financial Knowledge Graph — NetworkX-based graph intelligence layer.
Detects fraud networks: circular trading loops, shell companies,
promoter-linked fraud, suspicious vendor clusters.
"""

import networkx as nx
from typing import Any


class FinancialKnowledgeGraph:
    """
    Builds and analyzes a financial knowledge graph.
    Nodes: Company, Director, Promoter, Subsidiary, Supplier, Customer, Legal Case, Bank Loan
    Edges: owns, controls, supplies, litigated, defaulted, invoice_to, payment_to
    """

    NODE_TYPES = [
        "company", "director", "promoter", "subsidiary",
        "supplier", "customer", "legal_case", "bank_loan",
        "gst_entity", "bank_account",
    ]

    EDGE_TYPES = [
        "owns", "controls", "supplies", "litigated", "defaulted",
        "invoice_to", "payment_to", "directorship", "loan_transfer",
    ]

    def __init__(self):
        self.graph = nx.DiGraph()
        self._fraud_signals = []

    def add_entity(self, entity_id: str, entity_type: str, **attrs) -> None:
        """Add a node to the knowledge graph."""
        self.graph.add_node(entity_id, type=entity_type, **attrs)

    def add_relationship(
        self, source: str, target: str, rel_type: str, **attrs
    ) -> None:
        """Add an edge (relationship) between two entities."""
        self.graph.add_edge(source, target, relationship=rel_type, **attrs)

    def build_from_financial_data(self, session_data: dict) -> None:
        """
        Auto-construct graph from extracted session data.
        Parses company info, directors, suppliers, customers, etc.
        """
        company = session_data.get("company_name", "Borrower")
        cin = session_data.get("cin", "")
        gstin = session_data.get("gstin", "")

        # Core company node
        self.add_entity(company, "company", cin=cin, gstin=gstin)

        # Extract directors/promoters from unstructured data
        fin_data = session_data.get("financial_data", {})

        # Add supplier/customer nodes from GST data
        suppliers = fin_data.get("suppliers", [])
        for s in suppliers if isinstance(suppliers, list) else []:
            name = s if isinstance(s, str) else s.get("name", f"Supplier_{id(s)}")
            self.add_entity(name, "supplier")
            self.add_relationship(name, company, "supplies", invoice_count=1)

        customers = fin_data.get("customers", [])
        for c in customers if isinstance(customers, list) else []:
            name = c if isinstance(c, str) else c.get("name", f"Customer_{id(c)}")
            self.add_entity(name, "customer")
            self.add_relationship(company, name, "invoice_to", invoice_count=1)

        # Directors
        directors = fin_data.get("directors", [])
        for d in directors if isinstance(directors, list) else []:
            name = d if isinstance(d, str) else d.get("name", f"Director_{id(d)}")
            self.add_entity(name, "director")
            self.add_relationship(name, company, "directorship")

        # Promoters
        promoters = fin_data.get("promoters", [])
        for p in promoters if isinstance(promoters, list) else []:
            name = p if isinstance(p, str) else p.get("name", f"Promoter_{id(p)}")
            self.add_entity(name, "promoter")
            self.add_relationship(name, company, "owns")

    def detect_circular_trading(self) -> list[dict]:
        """
        Detect circular trading loops in the transaction graph.
        Looks for cycles: A → B → C → A where all edges are invoice_to or supplies.
        """
        cycles = []
        try:
            all_cycles = list(nx.simple_cycles(self.graph))
            for cycle in all_cycles:
                if len(cycle) >= 3:
                    # Check if cycle edges are transaction-related
                    is_trading_cycle = True
                    for i in range(len(cycle)):
                        src = cycle[i]
                        tgt = cycle[(i + 1) % len(cycle)]
                        edge = self.graph.get_edge_data(src, tgt, {})
                        rel = edge.get("relationship", "")
                        if rel not in ("invoice_to", "supplies", "payment_to"):
                            is_trading_cycle = False
                            break
                    if is_trading_cycle:
                        cycles.append({
                            "type": "circular_trading",
                            "entities": cycle,
                            "description": f"Circular trading loop: {' → '.join(cycle)} → {cycle[0]}",
                            "risk_level": "HIGH",
                        })
        except Exception:
            pass
        return cycles

    def detect_shell_companies(self) -> list[dict]:
        """
        Detect shell company patterns:
        - High invoice volume but low employee count / minimal tax
        - Entities with no real operational activity
        """
        shells = []
        for node, data in self.graph.nodes(data=True):
            if data.get("type") in ("supplier", "customer", "company"):
                in_degree = self.graph.in_degree(node)
                out_degree = self.graph.out_degree(node)
                employee_count = data.get("employee_count", None)
                tax_paid = data.get("tax_paid", None)
                invoice_volume = data.get("invoice_volume", in_degree + out_degree)

                if employee_count is not None and invoice_volume > 0:
                    if employee_count < 5 and invoice_volume > 10:
                        shells.append({
                            "type": "shell_company",
                            "entity": node,
                            "description": f"Potential shell company: {node} — {employee_count} employees but {invoice_volume} invoices",
                            "risk_level": "HIGH",
                            "employee_count": employee_count,
                            "invoice_volume": invoice_volume,
                        })

                if tax_paid is not None and invoice_volume > 0:
                    if tax_paid < 1000 and invoice_volume > 5:
                        shells.append({
                            "type": "shell_company",
                            "entity": node,
                            "description": f"Potential shell: {node} — ₹{tax_paid} tax on {invoice_volume} invoices",
                            "risk_level": "MEDIUM",
                        })
        return shells

    def detect_suspicious_vendor_clusters(self) -> list[dict]:
        """
        Detect clusters of vendors with similar patterns
        (shared addresses, similar names, connected promoters).
        """
        clusters = []
        suppliers = [
            n for n, d in self.graph.nodes(data=True)
            if d.get("type") == "supplier"
        ]

        # Group by shared promoters/directors
        promoter_map = {}
        for supplier in suppliers:
            for pred in self.graph.predecessors(supplier):
                edge = self.graph.get_edge_data(pred, supplier, {})
                if edge.get("relationship") in ("owns", "controls", "directorship"):
                    promoter_map.setdefault(pred, []).append(supplier)

        for promoter, linked_suppliers in promoter_map.items():
            if len(linked_suppliers) >= 2:
                clusters.append({
                    "type": "suspicious_vendor_cluster",
                    "promoter": promoter,
                    "vendors": linked_suppliers,
                    "description": f"Shared promoter '{promoter}' controls {len(linked_suppliers)} supplier entities",
                    "risk_level": "HIGH",
                })

        return clusters

    def detect_fund_diversion(self) -> list[dict]:
        """Detect promoter fund diversion patterns."""
        diversions = []
        promoters = [
            n for n, d in self.graph.nodes(data=True)
            if d.get("type") == "promoter"
        ]

        for promoter in promoters:
            # Check if promoter has payment relationships outside company
            for succ in self.graph.successors(promoter):
                edge = self.graph.get_edge_data(promoter, succ, {})
                if edge.get("relationship") == "payment_to":
                    succ_data = self.graph.nodes.get(succ, {})
                    if succ_data.get("type") not in ("company",):
                        diversions.append({
                            "type": "fund_diversion",
                            "promoter": promoter,
                            "recipient": succ,
                            "description": f"Potential fund diversion: {promoter} → {succ}",
                            "risk_level": "HIGH",
                        })
        return diversions

    def compute_risk_propagation(self) -> dict:
        """
        Compute risk propagation scores using PageRank-like algorithm.
        Higher centrality = higher systemic risk.
        """
        try:
            pagerank = nx.pagerank(self.graph, alpha=0.85)
            betweenness = nx.betweenness_centrality(self.graph)
            return {
                "pagerank": {k: round(v, 4) for k, v in sorted(
                    pagerank.items(), key=lambda x: -x[1]
                )[:10]},
                "betweenness_centrality": {k: round(v, 4) for k, v in sorted(
                    betweenness.items(), key=lambda x: -x[1]
                )[:10]},
                "node_count": self.graph.number_of_nodes(),
                "edge_count": self.graph.number_of_edges(),
            }
        except Exception:
            return {
                "node_count": self.graph.number_of_nodes(),
                "edge_count": self.graph.number_of_edges(),
            }

    def run_full_analysis(self) -> dict:
        """Run all fraud detection analyses and return combined report."""
        circular = self.detect_circular_trading()
        shells = self.detect_shell_companies()
        clusters = self.detect_suspicious_vendor_clusters()
        diversions = self.detect_fund_diversion()
        risk = self.compute_risk_propagation()

        all_signals = circular + shells + clusters + diversions
        fraud_probability = min(1.0, len(all_signals) * 0.15)

        return {
            "circular_trading": circular,
            "shell_companies": shells,
            "vendor_clusters": clusters,
            "fund_diversions": diversions,
            "risk_propagation": risk,
            "total_signals": len(all_signals),
            "fraud_probability": round(fraud_probability, 2),
            "all_signals": all_signals,
        }

    def get_graph_summary(self) -> dict:
        """Return a summary of the knowledge graph for visualization."""
        nodes = []
        for n, d in self.graph.nodes(data=True):
            nodes.append({"id": n, "type": d.get("type", "unknown"), **{
                k: v for k, v in d.items() if k != "type"
            }})
        edges = []
        for u, v, d in self.graph.edges(data=True):
            edges.append({
                "source": u,
                "target": v,
                "relationship": d.get("relationship", "related"),
            })
        return {"nodes": nodes, "edges": edges}
