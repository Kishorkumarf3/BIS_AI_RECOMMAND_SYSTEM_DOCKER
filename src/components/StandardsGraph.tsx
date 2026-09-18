import { useCallback } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  addEdge,
  useNodesState,
  useEdgesState,
  type Node,
  type Edge,
  type Connection,
  BackgroundVariant,
} from "reactflow";
import "reactflow/dist/style.css";
import { Shield, FlaskConical, FileText, Ruler, Beaker } from "lucide-react";
import type { BISRecommendation, NormativeRef } from "@/types/bis";

interface StandardsGraphProps {
  standard: BISRecommendation;
}

const relationConfig: Record<
  NormativeRef["relation"],
  { color: string; icon: typeof Shield; label: string }
> = {
  testing: { color: "#0891b2", icon: FlaskConical, label: "Testing Standard" },
  safety: { color: "#dc2626", icon: Shield, label: "Safety Standard" },
  material: { color: "#16a34a", icon: FileText, label: "Material Spec" },
  method: { color: "#ca8a04", icon: Beaker, label: "Test Method" },
  dimensional: { color: "#7c3aed", icon: Ruler, label: "Dimensional" },
};

function createNodesAndEdges(standard: BISRecommendation): { nodes: Node[]; edges: Edge[] } {
  const nodes: Node[] = [];
  const edges: Edge[] = [];

  // Root node — the primary product standard
  nodes.push({
    id: standard.is_code,
    position: { x: 400, y: 250 },
    data: {
      label: (
        <div className="flex flex-col items-center gap-1 px-4 py-3">
          <div className="flex items-center gap-2">
            <FileText className="h-4 w-4 text-sky-400" />
            <span className="font-bold text-slate-900 text-sm">{standard.is_code}</span>
          </div>
          <span className="text-xs text-slate-600 max-w-[180px] text-center leading-tight">
            {standard.title}
          </span>
          <span className="mt-1 rounded-full bg-sky-100 px-2 py-0.5 text-[10px] font-semibold text-sky-700">
            Primary Standard
          </span>
        </div>
      ),
    },
    style: {
      background: "#f0f9ff",
      border: "2px solid #0ea5e9",
      borderRadius: "12px",
      width: 220,
    },
  });

  // Normative reference nodes arranged in a circle around root
  const refCount = standard.normative_refs.length;
  const radius = 220;

  standard.normative_refs.forEach((ref, i) => {
    const angle = (i / refCount) * 2 * Math.PI - Math.PI / 2;
    const x = 400 + radius * Math.cos(angle);
    const y = 250 + radius * Math.sin(angle);

    const config = relationConfig[ref.relation] || relationConfig.testing;
    const Icon = config.icon;

    nodes.push({
      id: ref.is_code,
      position: { x, y },
      data: {
        label: (
          <div className="flex flex-col items-center gap-1 px-3 py-2">
            <div className="flex items-center gap-1.5">
              <Icon className="h-3.5 w-3.5" style={{ color: config.color }} />
              <span className="font-semibold text-slate-800 text-xs">{ref.is_code}</span>
            </div>
            <span className="text-[10px] text-slate-600 max-w-[140px] text-center leading-tight">
              {ref.title}
            </span>
            <span
              className="mt-0.5 rounded-full px-2 py-0.5 text-[9px] font-medium"
              style={{
                background: `${config.color}1a`,
                color: config.color,
              }}
            >
              {config.label}
            </span>
          </div>
        ),
      },
      style: {
        background: "#ffffff",
        border: `1.5px solid ${config.color}40`,
        borderRadius: "10px",
        width: 170,
      },
    });

    edges.push({
      id: `e-${standard.is_code}-${ref.is_code}`,
      source: standard.is_code,
      target: ref.is_code,
      animated: true,
      style: { stroke: config.color, strokeWidth: 1.5 },
    });
  });

  return { nodes, edges };
}

export default function StandardsGraph({ standard }: StandardsGraphProps) {
  const { nodes: initialNodes, edges: initialEdges } = createNodesAndEdges(standard);
  const [nodes, , onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  const onConnect = useCallback(
    (connection: Connection) => setEdges((eds) => addEdge(connection, eds)),
    [setEdges]
  );

  return (
    <div className="h-[420px] w-full rounded-xl border border-slate-200 bg-slate-50">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        fitView
        fitViewOptions={{ padding: 0.2 }}
        attributionPosition="bottom-left"
        proOptions={{ hideAttribution: true }}
      >
        <Background variant={BackgroundVariant.Dots} gap={20} size={1} color="#cbd5e1" />
        <Controls
          showInteractive={false}
          className="!border-slate-200 !shadow-md !rounded-lg"
        />
        <MiniMap
          nodeColor={(node) => {
            if (node.id === standard.is_code) return "#0ea5e9";
            return "#94a3b8";
          }}
          maskColor="rgba(241, 245, 249, 0.7)"
          className="!bg-white !border !border-slate-200 !rounded-lg"
        />
      </ReactFlow>
    </div>
  );
}
