'use client';

import { memo, useEffect, useId, useMemo, useState } from 'react';
import styles from './dialoguePage.module.css';
import type { KnowledgeGraphData } from '../lib/dialogue-types';

type KnowledgeGraphMessageProps = {
  graph: KnowledgeGraphData;
};

type PreparedGraphEdge = {
  id: string;
  label: string;
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  labelX: number;
  labelY: number;
};

const MAX_ANIMATED_NODES = 36;
const MAX_ANIMATED_EDGES = 56;
const REVEAL_FRAME_BUDGET = 18;

function getRevealBatchSize(total: number) {
  return Math.max(1, Math.ceil(total / REVEAL_FRAME_BUDGET));
}

function getRevealInterval(total: number) {
  if (total <= 12) {
    return 180;
  }

  if (total <= 48) {
    return 96;
  }

  return 48;
}

const KnowledgeGraphMessage = memo(function KnowledgeGraphMessage({ graph }: KnowledgeGraphMessageProps) {
  const patternId = useId();
  const [visibleNodes, setVisibleNodes] = useState(0);
  const [visibleEdges, setVisibleEdges] = useState(0);

  const preparedGraph = useMemo(() => {
    const nodeMap = new Map(graph.nodes.map((node) => [node.id, node]));
    const preparedEdges: PreparedGraphEdge[] = [];

    for (const edge of graph.edges) {
      const from = nodeMap.get(edge.from);
      const to = nodeMap.get(edge.to);

      if (!from || !to) {
        continue;
      }

      preparedEdges.push({
        id: edge.id,
        label: edge.label,
        x1: from.x,
        y1: from.y,
        x2: to.x,
        y2: to.y,
        labelX: (from.x + to.x) / 2,
        labelY: (from.y + to.y) / 2,
      });
    }

    return {
      nodes: graph.nodes,
      edges: preparedEdges,
      showNodeLabels: graph.nodes.length <= 42,
      showEdgeLabels: preparedEdges.length <= 28,
      animateNodes: graph.nodes.length <= MAX_ANIMATED_NODES,
      animateEdges: preparedEdges.length <= MAX_ANIMATED_EDGES,
    };
  }, [graph.edges, graph.nodes]);

  const totalNodes = preparedGraph.nodes.length;
  const totalEdges = preparedGraph.edges.length;
  const nodeBatchSize = useMemo(() => getRevealBatchSize(totalNodes), [totalNodes]);
  const edgeBatchSize = useMemo(() => getRevealBatchSize(totalEdges), [totalEdges]);
  const nodeInterval = useMemo(() => getRevealInterval(totalNodes), [totalNodes]);
  const edgeInterval = useMemo(() => getRevealInterval(totalEdges), [totalEdges]);

  useEffect(() => {
    setVisibleNodes(0);
    setVisibleEdges(0);

    let nodeTimer = 0;
    let edgeTimer = 0;

    const revealNodes = (nextCount: number) => {
      setVisibleNodes(nextCount);

      if (nextCount >= totalNodes) {
        return;
      }

      nodeTimer = window.setTimeout(() => {
        revealNodes(Math.min(totalNodes, nextCount + nodeBatchSize));
      }, nodeInterval);
    };

    const revealEdges = (nextCount: number) => {
      setVisibleEdges(nextCount);

      if (nextCount >= totalEdges) {
        return;
      }

      edgeTimer = window.setTimeout(() => {
        revealEdges(Math.min(totalEdges, nextCount + edgeBatchSize));
      }, edgeInterval);
    };

    if (totalNodes > 0) {
      nodeTimer = window.setTimeout(() => {
        revealNodes(Math.min(totalNodes, nodeBatchSize));
      }, nodeInterval);
    }

    if (totalEdges > 0) {
      const edgeStartDelay = Math.min(640, Math.max(140, nodeInterval * Math.min(4, Math.ceil(totalNodes / Math.max(nodeBatchSize, 1)))));
      edgeTimer = window.setTimeout(() => {
        revealEdges(Math.min(totalEdges, edgeBatchSize));
      }, edgeStartDelay);
    }

    return () => {
      window.clearTimeout(nodeTimer);
      window.clearTimeout(edgeTimer);
    };
  }, [edgeBatchSize, edgeInterval, nodeBatchSize, nodeInterval, totalEdges, totalNodes]);

  const activeNodes = useMemo(() => preparedGraph.nodes.slice(0, visibleNodes), [preparedGraph.nodes, visibleNodes]);
  const activeEdges = useMemo(() => preparedGraph.edges.slice(0, visibleEdges), [preparedGraph.edges, visibleEdges]);

  return (
    <div className={styles.graphCanvas}>
      <div className={styles.graphStatus}>
        <span>nodes {visibleNodes}/{totalNodes}</span>
        <span>edges {visibleEdges}/{totalEdges}</span>
      </div>
      <svg viewBox="0 0 760 430" className={styles.graphSvg} role="img" aria-label="Knowledge graph preview">
        <defs>
          <pattern id={patternId} width="26" height="26" patternUnits="userSpaceOnUse">
            <circle cx="2" cy="2" r="1.4" fill="rgba(137, 151, 181, 0.22)" />
          </pattern>
        </defs>
        <rect width="760" height="430" fill={`url(#${patternId})`} />

        {activeEdges.map((edge) => (
          <g
            key={edge.id}
            className={preparedGraph.animateEdges ? styles.graphEdge : styles.graphEdgeStatic}
          >
            <line x1={edge.x1} y1={edge.y1} x2={edge.x2} y2={edge.y2} vectorEffect="non-scaling-stroke" />
            {preparedGraph.showEdgeLabels ? <text x={edge.labelX} y={edge.labelY - 8}>{edge.label}</text> : null}
          </g>
        ))}

        {activeNodes.map((node) => (
          <g
            key={node.id}
            transform={`translate(${node.x}, ${node.y})`}
            className={preparedGraph.animateNodes ? styles.graphNode : styles.graphNodeStatic}
          >
            <circle r="10" fill={node.color} />
            {preparedGraph.showNodeLabels ? <text x="16" y="5">{node.label}</text> : null}
          </g>
        ))}
      </svg>
    </div>
  );
});

export default KnowledgeGraphMessage;
