"use client";

import React, { useRef, useState, useCallback } from "react";
import dynamic from "next/dynamic";
import SpriteText from "three-spritetext";

// react-force-graph-3d touches `window`/WebGL at import time, so it must be
// loaded client-side only — ssr:false avoids the Next.js server trying to
// render it during build/SSR.
const ForceGraph3D = dynamic(() => import("react-force-graph-3d"), { ssr: false });

// Color by node type. Keep this in sync with logs_to_graph.py node "type" field.
const TYPE_COLOR = {
  vendor: "#7F77DD",   // purple
  function: "#378ADD", // blue
  document: "#1D9E75", // teal
  error: "#E24B4A",    // red
};

const TYPE_SIZE = {
  vendor: 14,
  function: 5,
  document: 8,
  error: 7,
};

// What each node type *means* — shown in the left panel so a viewer who has
// never seen this pipeline can understand the graph without hovering.
const TYPE_MEANING = {
  vendor: "Root of one vendor's onboarding run. Every event traces back to this.",
  function: "A module:function in the codebase that logged an event (e.g. core.tasks:parse_and_vectorize_document). Edges between functions show the order control actually passed through them.",
  document: "A document type that was uploaded and processed (MSA, PCI_DSS_AOC, SOC2_TYPE2). Linked to whichever function touched it.",
  error: "An ERROR/CRITICAL log line. Linked to the function that raised it, labeled with the failure message.",
};

export default function VendorPipelineGraph3D({ graphDataUrl = "/graph.json" }) {
  const fgRef = useRef(null);
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const [hoverNode, setHoverNode] = useState(null);
  const [status, setStatus] = useState("idle"); // idle | loading | error | ready

  const buildGraph = useCallback(() => {
    setStatus("loading");
    setGraphData({ nodes: [], links: [] });

    fetch(graphDataUrl)
      .then((res) => res.json())
      .then((fullData) => {
        const { nodes, links } = fullData;
        const totalSteps = nodes.length + links.length;
        if (totalSteps === 0) {
          setGraphData(fullData);
          setStatus("ready");
          return;
        }

        // Spread node+link insertion across ~10 seconds so the graph visibly
        // grows piece by piece instead of popping in all at once.
        const totalDurationMs = 10000;
        const stepDelay = totalDurationMs / totalSteps;

        let nodeCount = 0;
        let linkCount = 0;
        let step = 0;

        const interval = setInterval(() => {
          step += 1;

          // Add a node first if any remain, then a link, alternating roughly
          // so links appear once their endpoint nodes are likely present.
          if (nodeCount < nodes.length && (step % 2 === 1 || linkCount >= links.length)) {
            nodeCount += 1;
          } else if (linkCount < links.length) {
            linkCount += 1;
          } else if (nodeCount < nodes.length) {
            nodeCount += 1;
          }

          const visibleNodeIds = new Set(nodes.slice(0, nodeCount).map((n) => n.id));
          const visibleLinks = links
            .slice(0, linkCount)
            .filter((l) => visibleNodeIds.has(l.source) && visibleNodeIds.has(l.target || l.target?.id));

          setGraphData({
            nodes: nodes.slice(0, nodeCount),
            links: visibleLinks,
          });

          if (nodeCount >= nodes.length && linkCount >= links.length) {
            clearInterval(interval);
            setGraphData(fullData); // ensure final state matches source exactly
            setStatus("ready");
          }
        }, stepDelay);
      })
      .catch((err) => {
        console.error("Failed to load graph data:", err);
        setStatus("error");
      });
  }, [graphDataUrl]);

  return (
    <div style={{ width: "100%", height: "100vh", position: "relative", display: "flex" }}>
      {/* Left legend panel */}
      <div
        style={{
          width: 280,
          flexShrink: 0,
          background: "#111",
          color: "#eee",
          padding: "20px 16px",
          overflowY: "auto",
          borderRight: "1px solid #2a2a2a",
        }}
      >
        <h3 style={{ margin: "0 0 4px", fontSize: 16, fontWeight: 500 }}>Vendor pipeline graph</h3>
        <p style={{ margin: "0 0 16px", fontSize: 12, color: "#999" }}>
          Each node is something that happened during onboarding processing. Colors group nodes by type.
        </p>

        <button
          onClick={buildGraph}
          disabled={status === "loading"}
          style={{
            width: "100%",
            padding: "10px 12px",
            marginBottom: 20,
            background: status === "loading" ? "#333" : "#378ADD",
            color: "#fff",
            border: "none",
            borderRadius: 8,
            fontSize: 14,
            cursor: status === "loading" ? "default" : "pointer",
          }}
        >
          {status === "loading" ? "Building graph…" : status === "ready" ? "Rebuild graph" : "Build graph"}
        </button>

        {status === "error" && (
          <p style={{ fontSize: 12, color: "#E24B4A", marginBottom: 16 }}>
            Couldn't load {graphDataUrl}. Check the file exists and the path is correct.
          </p>
        )}

        <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          {Object.entries(TYPE_COLOR).map(([type, color]) => (
            <div key={type}>
              <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
                <span style={{ width: 10, height: 10, borderRadius: "50%", background: color, flexShrink: 0 }} />
                <span style={{ fontSize: 13, fontWeight: 500, textTransform: "capitalize" }}>{type}</span>
              </div>
              <p style={{ margin: 0, fontSize: 11.5, lineHeight: 1.5, color: "#aaa" }}>{TYPE_MEANING[type]}</p>
            </div>
          ))}
        </div>

        {hoverNode && (
          <div style={{ marginTop: 24, paddingTop: 16, borderTop: "1px solid #2a2a2a" }}>
            <p style={{ fontSize: 11, color: "#777", margin: "0 0 6px" }}>Selected node</p>
            <p style={{ fontSize: 13, fontWeight: 500, margin: "0 0 4px", wordBreak: "break-word" }}>{hoverNode.label}</p>
            <p style={{ fontSize: 11.5, color: "#999", margin: 0 }}>type: {hoverNode.type}</p>
            {hoverNode.full_message && (
              <p style={{ fontSize: 11.5, color: "#ccc", marginTop: 6, lineHeight: 1.5 }}>{hoverNode.full_message}</p>
            )}
          </div>
        )}
      </div>

      {/* Graph canvas */}
      <div style={{ flex: 1, position: "relative" }}>
        {status === "idle" && (
          <div
            style={{
              position: "absolute",
              inset: 0,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "#666",
              fontSize: 14,
              background: "#0a0a0a",
            }}
          >
            Click "Build graph" to render
          </div>
        )}

        {(status === "loading" || status === "ready") && (
          <ForceGraph3D
            ref={fgRef}
            graphData={graphData}
            backgroundColor="#0a0a0a"
            nodeColor={(node) => TYPE_COLOR[node.type] || "#999"}
            nodeVal={(node) => TYPE_SIZE[node.type] || 5}
            nodeOpacity={0.95}
            // Always-visible text label above each node, instead of hover-only nodeLabel.
            nodeThreeObject={(node) => {
              const sprite = new SpriteText(node.label);
              sprite.color = TYPE_COLOR[node.type] || "#fff";
              sprite.textHeight = node.type === "vendor" ? 6 : 3.5;
              sprite.position.set(0, (TYPE_SIZE[node.type] || 5) + 4, 0); // float above the node sphere
              return sprite;
            }}
            nodeThreeObjectExtend={true} // keep the sphere AND add the label, instead of replacing it
            linkColor={(link) =>
              link.type === "raises" ? "#E24B4A" : link.type === "touches" ? "#1D9E75" : "#888"
            }
            linkWidth={(link) => Math.min(1 + (link.weight || 1) * 0.3, 4)}
            linkDirectionalArrowLength={4}
            linkDirectionalArrowRelPos={1}
            linkOpacity={0.4}
            onNodeHover={setHoverNode}
            onNodeClick={(node) => {
              const distance = 80;
              const distRatio = 1 + distance / Math.hypot(node.x, node.y, node.z);
              fgRef.current.cameraPosition(
                { x: node.x * distRatio, y: node.y * distRatio, z: node.z * distRatio },
                node,
                1000
              );
            }}
          />
        )}
      </div>
    </div>
  );
}