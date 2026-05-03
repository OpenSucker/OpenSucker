'use client';

import { memo, useEffect, useRef, useState } from 'react';
import styles from './dialoguePage.module.css';
import type { KnowledgeGraphData } from '../lib/dialogue-types';

type Props = { graph: KnowledgeGraphData };

type SimNode = {
  id: string;
  label: string;
  color: string;
  x?: number;
  y?: number;
  fx?: number | null;
  fy?: number | null;
  vx?: number;
  vy?: number;
  index?: number;
};

type SimLink = {
  source: SimNode;
  target: SimNode;
  label: string;
  id: string;
};

export default memo(function KnowledgeGraphMessage({ graph }: Props) {
  const svgRef = useRef<SVGSVGElement>(null);
  const [counts, setCounts] = useState({ nodes: 0, edges: 0 });

  useEffect(() => {
    const el = svgRef.current;
    if (!el) return;

    let stopped = false;

    void import('d3').then((d3) => {
      if (stopped || !svgRef.current) return;

      const width = 760;
      const height = 420;
      const svg = d3.select(el);
      svg.selectAll('*').remove();

      const defs = svg.append('defs');

      // arrowhead
      defs.append('marker')
        .attr('id', 'kg-arrow')
        .attr('viewBox', '0 -4 8 8')
        .attr('refX', 20)
        .attr('refY', 0)
        .attr('markerWidth', 6)
        .attr('markerHeight', 6)
        .attr('orient', 'auto')
        .append('path')
        .attr('d', 'M0,-4L8,0L0,4')
        .attr('fill', 'rgba(0,0,0,0.22)');

      // dot-grid background
      const pid = `kg-dots-${Math.random().toString(36).slice(2, 7)}`;
      const pat = defs.append('pattern')
        .attr('id', pid).attr('width', 26).attr('height', 26)
        .attr('patternUnits', 'userSpaceOnUse');
      pat.append('circle').attr('cx', 2).attr('cy', 2).attr('r', 1.4)
        .attr('fill', 'rgba(137,151,181,0.22)');
      svg.append('rect').attr('width', width).attr('height', height)
        .attr('fill', `url(#${pid})`);

      // zoom container
      const g = svg.append('g');
      svg.call(
        d3.zoom<SVGSVGElement, unknown>()
          .scaleExtent([0.15, 4])
          .on('zoom', (ev) => g.attr('transform', ev.transform)),
      );

      // clone node/link data (D3 mutates in place)
      const nodes: SimNode[] = graph.nodes.map((n) => ({
        id: n.id, label: n.label, color: n.color, x: n.x, y: n.y,
      }));
      const nodeById = new Map(nodes.map((n) => [n.id, n]));
      const links: SimLink[] = graph.edges
        .filter((e) => nodeById.has(e.from) && nodeById.has(e.to))
        .map((e) => ({
          source: nodeById.get(e.from)!,
          target: nodeById.get(e.to)!,
          label: e.label,
          id: e.id,
        }));

      setCounts({ nodes: nodes.length, edges: links.length });

      const simulation = d3.forceSimulation<SimNode>(nodes)
        .force('link', d3.forceLink<SimNode, SimLink>(links)
          .id((d) => d.id).distance(88).strength(0.55))
        .force('charge', d3.forceManyBody<SimNode>().strength(-220))
        .force('center', d3.forceCenter(width / 2, height / 2))
        .force('collide', d3.forceCollide<SimNode>(28));

      // edges
      const linkSel = g.append('g')
        .selectAll<SVGLineElement, SimLink>('line')
        .data(links).join('line')
        .attr('stroke', 'rgba(0,0,0,0.18)')
        .attr('stroke-width', 1.5)
        .attr('marker-end', 'url(#kg-arrow)');

      // edge labels (≤28 edges)
      const showEdgeLabels = links.length <= 28;
      const edgeLabelSel = showEdgeLabels
        ? g.append('g')
            .selectAll<SVGGElement, SimLink>('g')
            .data(links).join('g')
        : null;

      if (edgeLabelSel) {
        edgeLabelSel.append('rect')
          .attr('rx', 3).attr('fill', 'rgba(239,237,228,0.9)')
          .attr('stroke', 'rgba(0,0,0,0.08)').attr('stroke-width', 0.8);
        const textSel = edgeLabelSel.append('text')
          .attr('text-anchor', 'middle').attr('dominant-baseline', 'middle')
          .attr('fill', 'rgba(0,0,0,0.4)').attr('font-size', 9)
          .attr('font-family', 'monospace')
          .text((d) => d.label);
        // size background rects
        textSel.each(function () {
          const parent = d3.select(this.parentNode as Element);
          try {
            const bbox = (this as SVGTextElement).getBBox();
            parent.select('rect')
              .attr('x', bbox.x - 3).attr('y', bbox.y - 2)
              .attr('width', bbox.width + 6).attr('height', bbox.height + 4);
          } catch { /* getBBox unavailable in test env */ }
        });
      }

      // nodes
      const drag = d3.drag<SVGGElement, SimNode>()
        .on('start', (ev, d) => {
          if (!ev.active) simulation.alphaTarget(0.3).restart();
          d.fx = d.x; d.fy = d.y;
        })
        .on('drag', (ev, d) => { d.fx = ev.x; d.fy = ev.y; })
        .on('end', (ev, d) => {
          if (!ev.active) simulation.alphaTarget(0);
          d.fx = null; d.fy = null;
        });

      const nodeSel = g.append('g')
        .selectAll<SVGGElement, SimNode>('g')
        .data(nodes).join('g')
        .style('cursor', 'grab')
        .call(drag);

      nodeSel.append('circle')
        .attr('r', 10).attr('fill', (d) => d.color)
        .attr('stroke', '#000').attr('stroke-width', 1.5);

      if (nodes.length <= 42) {
        nodeSel.append('text')
          .attr('x', 14).attr('y', 4).attr('font-size', 11)
          .attr('font-family', 'var(--font-geist-sans),Arial,sans-serif')
          .attr('fill', '#111')
          .text((d) => d.label);
      }

      simulation.on('tick', () => {
        linkSel
          .attr('x1', (d) => (d.source as SimNode).x ?? 0)
          .attr('y1', (d) => (d.source as SimNode).y ?? 0)
          .attr('x2', (d) => (d.target as SimNode).x ?? 0)
          .attr('y2', (d) => (d.target as SimNode).y ?? 0);

        edgeLabelSel?.attr('transform', (d) => {
          const mx = ((d.source as SimNode).x! + (d.target as SimNode).x!) / 2;
          const my = ((d.source as SimNode).y! + (d.target as SimNode).y!) / 2;
          return `translate(${mx},${my})`;
        });

        nodeSel.attr('transform', (d) => `translate(${d.x ?? 0},${d.y ?? 0})`);
      });
    });

    return () => {
      stopped = true;
    };
  }, [graph]);

  return (
    <div className={styles.graphCanvas}>
      <div className={styles.graphStatus}>
        <span>nodes {counts.nodes}/{graph.nodes.length}</span>
        <span>edges {counts.edges}/{graph.edges.length}</span>
        <span className={styles.graphHint}>可拖拽 · 滚轮缩放</span>
      </div>
      <svg
        ref={svgRef}
        viewBox="0 0 760 420"
        className={styles.graphSvg}
        role="img"
        aria-label="知识图谱"
      />
    </div>
  );
});
