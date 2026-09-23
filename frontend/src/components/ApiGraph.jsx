import { useEffect, useRef } from 'react';
import * as d3 from 'd3';

export default function ApiGraph({ endpoints }) {
  const svgRef = useRef(null);
  const containerRef = useRef(null);

  useEffect(() => {
    if (!endpoints.length || !svgRef.current || !containerRef.current) return;

    const container = containerRef.current;
    const width = container.clientWidth || 800;
    const height = container.clientHeight || 500;

    // Clear previous
    d3.select(svgRef.current).selectAll('*').remove();

    const svg = d3.select(svgRef.current)
      .attr('width', width)
      .attr('height', height);

    // Build nodes and links
    const methodColors = {
      GET: '#30d158',
      POST: '#0071e3',
      PUT: '#ff9f0a',
      PATCH: '#bf5af2',
      DELETE: '#ff453a',
    };

    // Group endpoints by base path (resource)
    const resources = {};
    endpoints.forEach(ep => {
      const parts = ep.path.split('/').filter(p => p && !p.startsWith('{') && !p.startsWith(':') && !p.startsWith('<'));
      const resource = parts.length > 1 ? parts.slice(0, 2).join('/') : parts[0] || 'root';
      if (!resources[resource]) resources[resource] = [];
      resources[resource].push(ep);
    });

    const nodes = [];
    const links = [];

    // Center node
    nodes.push({
      id: 'API',
      label: 'API',
      type: 'root',
      color: '#64d2ff',
      radius: 24,
    });

    // Resource nodes
    Object.keys(resources).forEach(resource => {
      const resourceId = `resource-${resource}`;
      nodes.push({
        id: resourceId,
        label: `/${resource}`,
        type: 'resource',
        color: '#f5f5f7',
        radius: 18,
      });
      links.push({ source: 'API', target: resourceId });

      // Endpoint nodes
      resources[resource].forEach((ep, i) => {
        const epId = `${ep.method}-${ep.path}-${i}`;
        nodes.push({
          id: epId,
          label: `${ep.method} ${ep.path}`,
          type: 'endpoint',
          method: ep.method,
          color: methodColors[ep.method] || '#6e6e73',
          radius: 12,
          endpoint: ep,
        });
        links.push({ source: resourceId, target: epId });
      });
    });

    // Simulation
    const simulation = d3.forceSimulation(nodes)
      .force('link', d3.forceLink(links).id(d => d.id).distance(d => {
        if (d.source.type === 'root') return 140;
        return 80;
      }))
      .force('charge', d3.forceManyBody().strength(d => {
        if (d.type === 'root') return -400;
        if (d.type === 'resource') return -200;
        return -100;
      }))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide(d => d.radius + 10));

    // Links
    const link = svg.append('g')
      .selectAll('line')
      .data(links)
      .join('line')
      .attr('class', 'graph-link')
      .attr('stroke', 'rgba(255,255,255,0.08)')
      .attr('stroke-width', 1.5);

    // Node groups
    const node = svg.append('g')
      .selectAll('g')
      .data(nodes)
      .join('g')
      .attr('class', 'graph-node')
      .call(d3.drag()
        .on('start', (event, d) => {
          if (!event.active) simulation.alphaTarget(0.3).restart();
          d.fx = d.x;
          d.fy = d.y;
        })
        .on('drag', (event, d) => {
          d.fx = event.x;
          d.fy = event.y;
        })
        .on('end', (event, d) => {
          if (!event.active) simulation.alphaTarget(0);
          d.fx = null;
          d.fy = null;
        })
      );

    // Glow filter
    const defs = svg.append('defs');
    const filter = defs.append('filter').attr('id', 'glow');
    filter.append('feGaussianBlur').attr('stdDeviation', 3).attr('result', 'coloredBlur');
    const feMerge = filter.append('feMerge');
    feMerge.append('feMergeNode').attr('in', 'coloredBlur');
    feMerge.append('feMergeNode').attr('in', 'SourceGraphic');

    // Circles
    node.append('circle')
      .attr('r', d => d.radius)
      .attr('fill', d => d.color)
      .attr('fill-opacity', d => d.type === 'endpoint' ? 0.8 : 1)
      .attr('stroke', d => d.color)
      .attr('stroke-width', d => d.type === 'root' ? 3 : 1.5)
      .attr('stroke-opacity', 0.3)
      .style('filter', d => d.type === 'root' ? 'url(#glow)' : 'none');

    // Labels
    node.append('text')
      .text(d => {
        if (d.type === 'root') return d.label;
        if (d.type === 'resource') return d.label;
        return d.method;
      })
      .attr('text-anchor', 'middle')
      .attr('dy', d => d.type === 'endpoint' ? '0.35em' : d.radius + 16)
      .attr('fill', d => d.type === 'endpoint' ? '#1d1d1f' : 'rgba(255,255,255,0.6)')
      .attr('font-size', d => d.type === 'endpoint' ? '8px' : '11px')
      .attr('font-weight', d => d.type === 'endpoint' ? '700' : '500')
      .attr('font-family', "'JetBrains Mono', monospace");

    // Path labels for endpoints
    node.filter(d => d.type === 'endpoint')
      .append('text')
      .text(d => d.endpoint?.path?.split('/').pop() || '')
      .attr('text-anchor', 'middle')
      .attr('dy', d => d.radius + 14)
      .attr('fill', 'rgba(255,255,255,0.4)')
      .attr('font-size', '9px')
      .attr('font-family', "'JetBrains Mono', monospace");

    // Tooltip
    node.append('title')
      .text(d => d.label);

    // Tick
    simulation.on('tick', () => {
      link
        .attr('x1', d => d.source.x)
        .attr('y1', d => d.source.y)
        .attr('x2', d => d.target.x)
        .attr('y2', d => d.target.y);

      node.attr('transform', d => `translate(${d.x},${d.y})`);
    });

    return () => simulation.stop();
  }, [endpoints]);

  if (!endpoints.length) {
    return (
      <div className="empty-state">
        <span className="empty-icon">🕸️</span>
        <h3>No endpoints to visualize</h3>
        <p>Generate docs first to see your API as an interactive graph</p>
      </div>
    );
  }

  return (
    <div className="api-graph" ref={containerRef}>
      <svg ref={svgRef}></svg>
    </div>
  );
}
