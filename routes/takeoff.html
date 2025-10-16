import React, { useState, useRef, useEffect } from 'react';
import { Ruler, Plus, Trash2, Save, FileText, Package, ZoomIn, ZoomOut, Move, MousePointer } from 'lucide-react';

// Mock data - in production, this would come from API
const MOCK_MATERIALS = [
  { id: 1, partNumber: 'PVC04020', category: 'PVC Sch 40 Pipe', description: '2" Sch 40 PVC Plain End Pipe', size: '2"', unit: 'LF', listPrice: 3.25, laborUnits: 0.10 },
  { id: 2, partNumber: 'PVC04030', category: 'PVC Sch 40 Pipe', description: '3" Sch 40 PVC Plain End Pipe', size: '3"', unit: 'LF', listPrice: 6.85, laborUnits: 0.14 },
  { id: 3, partNumber: 'PVC00404', category: 'PVC DWV Fittings', description: '2" PVC DWV 90° Elbow', size: '2"', unit: 'EA', listPrice: 2.85, laborUnits: 0.17 },
  { id: 4, partNumber: 'PVC00424', category: 'PVC DWV Fittings', description: '2" PVC DWV Sanitary Tee', size: '2"', unit: 'EA', listPrice: 4.50, laborUnits: 0.22 },
];

const MOCK_WBS = [
  { id: 1, name: 'Base Bid', children: [
    { id: 2, name: 'UG Water' },
    { id: 3, name: 'UG Sanitary' },
    { id: 4, name: 'UG Storm' },
    { id: 5, name: 'AG Water' },
    { id: 6, name: 'AG Sanitary' },
  ]},
];

const TakeoffMeasurementUI = () => {
  const canvasRef = useRef(null);
  const [tool, setTool] = useState('select'); // select, measure, count, pan
  const [scale, setScale] = useState({ name: '1/4" = 1\'-0"', ratio: 48 }); // 48:1 ratio
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  
  // Measurement state
  const [measurements, setMeasurements] = useState([]);
  const [currentMeasurement, setCurrentMeasurement] = useState(null);
  const [counts, setCounts] = useState([]);
  
  // Takeoff state
  const [takeoffItems, setTakeoffItems] = useState([]);
  const [showMaterialModal, setShowMaterialModal] = useState(false);
  const [selectedMaterial, setSelectedMaterial] = useState(null);
  const [selectedWBS, setSelectedWBS] = useState(null);
  const [quantity, setQuantity] = useState(0);
  const [multiplier, setMultiplier] = useState(1.0);
  
  // Drawing state
  const [isDragging, setIsDragging] = useState(false);
  const [lastPos, setLastPos] = useState({ x: 0, y: 0 });
  
  const [activeTab, setActiveTab] = useState('measure');
  
  // Canvas drawing
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Draw grid background
    ctx.save();
    ctx.translate(pan.x, pan.y);
    ctx.scale(zoom, zoom);
    
    // Grid
    ctx.strokeStyle = '#e0e0e0';
    ctx.lineWidth = 0.5;
    for (let x = 0; x < canvas.width / zoom; x += 50) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, canvas.height / zoom);
      ctx.stroke();
    }
    for (let y = 0; y < canvas.height / zoom; y += 50) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(canvas.width / zoom, y);
      ctx.stroke();
    }
    
    // Draw measurements
    ctx.strokeStyle = '#3b82f6';
    ctx.fillStyle = '#3b82f6';
    ctx.lineWidth = 2;
    ctx.font = '14px system-ui';
    
    measurements.forEach(m => {
      ctx.beginPath();
      ctx.moveTo(m.start.x, m.start.y);
      ctx.lineTo(m.end.x, m.end.y);
      ctx.stroke();
      
      // Draw endpoints
      ctx.beginPath();
      ctx.arc(m.start.x, m.start.y, 4, 0, Math.PI * 2);
      ctx.fill();
      ctx.beginPath();
      ctx.arc(m.end.x, m.end.y, 4, 0, Math.PI * 2);
      ctx.fill();
      
      // Draw length label
      const midX = (m.start.x + m.end.x) / 2;
      const midY = (m.start.y + m.end.y) / 2;
      ctx.fillStyle = 'white';
      ctx.fillRect(midX - 30, midY - 12, 60, 24);
      ctx.fillStyle = '#3b82f6';
      ctx.fillText(`${m.length.toFixed(1)}'`, midX - 20, midY + 4);
    });
    
    // Draw current measurement
    if (currentMeasurement) {
      ctx.strokeStyle = '#ef4444';
      ctx.lineWidth = 2;
      ctx.setLineDash([5, 5]);
      ctx.beginPath();
      ctx.moveTo(currentMeasurement.start.x, currentMeasurement.start.y);
      ctx.lineTo(currentMeasurement.end.x, currentMeasurement.end.y);
      ctx.stroke();
      ctx.setLineDash([]);
    }
    
    // Draw count markers
    ctx.fillStyle = '#10b981';
    counts.forEach((count, idx) => {
      ctx.beginPath();
      ctx.arc(count.x, count.y, 8, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillStyle = 'white';
      ctx.font = 'bold 12px system-ui';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText((idx + 1).toString(), count.x, count.y);
      ctx.fillStyle = '#10b981';
    });
    
    ctx.restore();
  }, [measurements, currentMeasurement, counts, zoom, pan]);
  
  const getCanvasCoords = (e) => {
    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    const x = (e.clientX - rect.left - pan.x) / zoom;
    const y = (e.clientY - rect.top - pan.y) / zoom;
    return { x, y };
  };
  
  const handleCanvasMouseDown = (e) => {
    const pos = getCanvasCoords(e);
    
    if (tool === 'measure') {
      setCurrentMeasurement({ start: pos, end: pos });
    } else if (tool === 'count') {
      setCounts([...counts, pos]);
    } else if (tool === 'pan') {
      setIsDragging(true);
      setLastPos({ x: e.clientX, y: e.clientY });
    }
  };
  
  const handleCanvasMouseMove = (e) => {
    if (tool === 'measure' && currentMeasurement) {
      const pos = getCanvasCoords(e);
      setCurrentMeasurement({ ...currentMeasurement, end: pos });
    } else if (tool === 'pan' && isDragging) {
      const dx = e.clientX - lastPos.x;
      const dy = e.clientY - lastPos.y;
      setPan({ x: pan.x + dx, y: pan.y + dy });
      setLastPos({ x: e.clientX, y: e.clientY });
    }
  };
  
  const handleCanvasMouseUp = (e) => {
    if (tool === 'measure' && currentMeasurement) {
      const pos = getCanvasCoords(e);
      const dx = pos.x - currentMeasurement.start.x;
      const dy = pos.y - currentMeasurement.start.y;
      const pixelLength = Math.sqrt(dx * dx + dy * dy);
      
      // Convert pixels to real-world length using scale
      const realLength = (pixelLength / scale.ratio) * 12; // Convert to feet
      
      setMeasurements([...measurements, {
        start: currentMeasurement.start,
        end: pos,
        length: realLength,
        pixelLength
      }]);
      setCurrentMeasurement(null);
    } else if (tool === 'pan') {
      setIsDragging(false);
    }
  };
  
  const clearMeasurements = () => {
    setMeasurements([]);
  };
  
  const clearCounts = () => {
    setCounts([]);
  };
  
  const addMeasurementToTakeoff = () => {
    if (measurements.length === 0) return;
    const totalLength = measurements.reduce((sum, m) => sum + m.length, 0);
    setQuantity(totalLength);
    setShowMaterialModal(true);
  };
  
  const addCountToTakeoff = () => {
    if (counts.length === 0) return;
    setQuantity(counts.length);
    setShowMaterialModal(true);
  };
  
  const saveTakeoffItem = () => {
    if (!selectedMaterial || !selectedWBS || !quantity) {
      alert('Please select material, WBS, and enter quantity');
      return;
    }
    
    const item = {
      id: Date.now(),
      material: selectedMaterial,
      wbs: selectedWBS,
      quantity,
      multiplier,
      extendedPrice: selectedMaterial.listPrice * quantity * multiplier,
      extendedLabor: selectedMaterial.laborUnits * quantity,
      measurementType: tool
    };
    
    setTakeoffItems([...takeoffItems, item]);
    setShowMaterialModal(false);
    setSelectedMaterial(null);
    setSelectedWBS(null);
    setQuantity(0);
    setMultiplier(1.0);
    
    // Clear measurements/counts after adding
    if (tool === 'measure') clearMeasurements();
    if (tool === 'count') clearCounts();
  };
  
  const deleteTakeoffItem = (id) => {
    setTakeoffItems(takeoffItems.filter(item => item.id !== id));
  };
  
  const generateRFQ = () => {
    // Group items by WBS and material
    const summary = {};
    
    takeoffItems.forEach(item => {
      const key = `${item.wbs.name}-${item.material.partNumber}`;
      if (!summary[key]) {
        summary[key] = {
          wbs: item.wbs.name,
          material: item.material,
          totalQuantity: 0,
          totalPrice: 0
        };
      }
      summary[key].totalQuantity += item.quantity * item.multiplier;
      summary[key].totalPrice += item.extendedPrice;
    });
    
    // In production, this would generate an actual RFQ document
    console.log('RFQ Summary:', summary);
    alert('RFQ generated! Check console for details.');
  };
  
  const totals = takeoffItems.reduce((acc, item) => ({
    materialCost: acc.materialCost + item.extendedPrice,
    laborHours: acc.laborHours + item.extendedLabor
  }), { materialCost: 0, laborHours: 0 });
  
  return (
    <div style={{ display: 'flex', height: '100vh', fontFamily: 'system-ui, -apple-system, sans-serif' }}>
      {/* Left Panel - Drawing Canvas */}
      <div style={{ flex: '1', display: 'flex', flexDirection: 'column', background: '#f8fafc' }}>
        {/* Toolbar */}
        <div style={{ padding: '12px', background: 'white', borderBottom: '1px solid #e2e8f0', display: 'flex', gap: '8px', alignItems: 'center' }}>
          <div style={{ display: 'flex', gap: '4px', marginRight: '16px' }}>
            <button
              onClick={() => setTool('select')}
              style={{
                padding: '8px 12px',
                background: tool === 'select' ? '#3b82f6' : 'white',
                color: tool === 'select' ? 'white' : '#64748b',
                border: '1px solid #e2e8f0',
                borderRadius: '6px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '6px'
              }}
              title="Select"
            >
              <MousePointer size={16} /> Select
            </button>
            <button
              onClick={() => setTool('measure')}
              style={{
                padding: '8px 12px',
                background: tool === 'measure' ? '#3b82f6' : 'white',
                color: tool === 'measure' ? 'white' : '#64748b',
                border: '1px solid #e2e8f0',
                borderRadius: '6px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '6px'
              }}
              title="Measure"
            >
              <Ruler size={16} /> Measure
            </button>
            <button
              onClick={() => setTool('count')}
              style={{
                padding: '8px 12px',
                background: tool === 'count' ? '#3b82f6' : 'white',
                color: tool === 'count' ? 'white' : '#64748b',
                border: '1px solid #e2e8f0',
                borderRadius: '6px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '6px'
              }}
              title="Count"
            >
              <Plus size={16} /> Count
            </button>
            <button
              onClick={() => setTool('pan')}
              style={{
                padding: '8px 12px',
                background: tool === 'pan' ? '#3b82f6' : 'white',
                color: tool === 'pan' ? 'white' : '#64748b',
                border: '1px solid #e2e8f0',
                borderRadius: '6px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '6px'
              }}
              title="Pan"
            >
              <Move size={16} /> Pan
            </button>
          </div>
          
          <div style={{ width: '1px', height: '24px', background: '#e2e8f0', margin: '0 8px' }} />
          
          <div style={{ display: 'flex', gap: '4px' }}>
            <button
              onClick={() => setZoom(Math.min(zoom + 0.2, 3))}
              style={{
                padding: '8px',
                background: 'white',
                border: '1px solid #e2e8f0',
                borderRadius: '6px',
                cursor: 'pointer'
              }}
              title="Zoom In"
            >
              <ZoomIn size={16} />
            </button>
            <button
              onClick={() => setZoom(Math.max(zoom - 0.2, 0.5))}
              style={{
                padding: '8px',
                background: 'white',
                border: '1px solid #e2e8f0',
                borderRadius: '6px',
                cursor: 'pointer'
              }}
              title="Zoom Out"
            >
              <ZoomOut size={16} />
            </button>
            <span style={{ padding: '8px 12px', color: '#64748b', fontSize: '14px' }}>
              {Math.round(zoom * 100)}%
            </span>
          </div>
          
          <div style={{ width: '1px', height: '24px', background: '#e2e8f0', margin: '0 8px' }} />
          
          <select
            value={scale.name}
            onChange={(e) => {
              const scales = {
                '1/8" = 1\'-0"': 96,
                '1/4" = 1\'-0"': 48,
                '1/2" = 1\'-0"': 24,
                '1" = 1\'-0"': 12
              };
              setScale({ name: e.target.value, ratio: scales[e.target.value] });
            }}
            style={{
              padding: '8px',
              border: '1px solid #e2e8f0',
              borderRadius: '6px',
              fontSize: '14px'
            }}
          >
            <option>1/8" = 1'-0"</option>
            <option>1/4" = 1'-0"</option>
            <option>1/2" = 1'-0"</option>
            <option>1" = 1'-0"</option>
          </select>
          
          <div style={{ flex: 1 }} />
          
          {measurements.length > 0 && (
            <>
              <span style={{ fontSize: '14px', color: '#64748b' }}>
                Total: {measurements.reduce((sum, m) => sum + m.length, 0).toFixed(1)} ft
              </span>
              <button
                onClick={addMeasurementToTakeoff}
                style={{
                  padding: '8px 16px',
                  background: '#10b981',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  fontWeight: '500'
                }}
              >
                <Package size={16} /> Add to Takeoff
              </button>
              <button
                onClick={clearMeasurements}
                style={{
                  padding: '8px 16px',
                  background: '#ef4444',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px'
                }}
              >
                Clear
              </button>
            </>
          )}
          
          {counts.length > 0 && (
            <>
              <span style={{ fontSize: '14px', color: '#64748b' }}>
                Count: {counts.length}
              </span>
              <button
                onClick={addCountToTakeoff}
                style={{
                  padding: '8px 16px',
                  background: '#10b981',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  fontWeight: '500'
                }}
              >
                <Package size={16} /> Add to Takeoff
              </button>
              <button
                onClick={clearCounts}
                style={{
                  padding: '8px 16px',
                  background: '#ef4444',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px'
                }}
              >
                Clear
              </button>
            </>
          )}
        </div>
        
        {/* Canvas */}
        <div style={{ flex: 1, position: 'relative', overflow: 'hidden' }}>
          <canvas
            ref={canvasRef}
            width={1200}
            height={800}
            onMouseDown={handleCanvasMouseDown}
            onMouseMove={handleCanvasMouseMove}
            onMouseUp={handleCanvasMouseUp}
            style={{
              width: '100%',
              height: '100%',
              cursor: tool === 'pan' ? 'grab' : tool === 'measure' ? 'crosshair' : tool === 'count' ? 'pointer' : 'default'
            }}
          />
        </div>
      </div>
      
      {/* Right Panel - Takeoff Sheet */}
      <div style={{ width: '500px', background: 'white', borderLeft: '1px solid #e2e8f0', display: 'flex', flexDirection: 'column' }}>
        <div style={{ padding: '16px', borderBottom: '1px solid #e2e8f0' }}>
          <h2 style={{ margin: '0 0 8px 0', fontSize: '20px', fontWeight: '600' }}>Takeoff Sheet</h2>
          <p style={{ margin: 0, fontSize: '14px', color: '#64748b' }}>
            Drawing: Sample Plan • Page 1
          </p>
        </div>
        
        {/* Takeoff Items */}
        <div style={{ flex: 1, overflow: 'auto', padding: '16px' }}>
          {takeoffItems.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '40px 20px', color: '#94a3b8' }}>
              <Package size={48} style={{ margin: '0 auto 16px', opacity: 0.5 }} />
              <p style={{ margin: 0 }}>No items yet. Use measurement tools to add materials.</p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {takeoffItems.map(item => (
                <div
                  key={item.id}
                  style={{
                    padding: '12px',
                    border: '1px solid #e2e8f0',
                    borderRadius: '8px',
                    background: '#f8fafc'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontWeight: '500', fontSize: '14px', marginBottom: '4px' }}>
                        {item.material.description}
                      </div>
                      <div style={{ fontSize: '13px', color: '#64748b' }}>
                        {item.material.partNumber} • {item.material.size}
                      </div>
                      <div style={{ fontSize: '12px', color: '#6366f1', marginTop: '4px' }}>
                        WBS: {item.wbs.name}
                      </div>
                    </div>
                    <button
                      onClick={() => deleteTakeoffItem(item.id)}
                      style={{
                        padding: '4px',
                        background: 'none',
                        border: 'none',
                        color: '#ef4444',
                        cursor: 'pointer'
                      }}
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                  
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', fontSize: '13px' }}>
                    <div>
                      <span style={{ color: '#64748b' }}>Qty:</span>{' '}
                      <strong>{item.quantity.toFixed(2)} {item.material.unit}</strong>
                    </div>
                    <div>
                      <span style={{ color: '#64748b' }}>Mult:</span>{' '}
                      <strong>{item.multiplier.toFixed(2)}</strong>
                    </div>
                    <div>
                      <span style={{ color: '#64748b' }}>Price:</span>{' '}
                      <strong>${item.extendedPrice.toFixed(2)}</strong>
                    </div>
                    <div>
                      <span style={{ color: '#64748b' }}>Labor:</span>{' '}
                      <strong>{item.extendedLabor.toFixed(2)} hrs</strong>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
        
        {/* Totals & Actions */}
        {takeoffItems.length > 0 && (
          <div style={{ borderTop: '1px solid #e2e8f0', padding: '16px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px', fontSize: '15px' }}>
              <span style={{ color: '#64748b' }}>Total Material:</span>
              <strong style={{ fontSize: '18px', color: '#3b82f6' }}>${totals.materialCost.toFixed(2)}</strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '16px', fontSize: '15px' }}>
              <span style={{ color: '#64748b' }}>Total Labor:</span>
              <strong style={{ fontSize: '18px', color: '#10b981' }}>{totals.laborHours.toFixed(2)} hrs</strong>
            </div>
            
            <button
              onClick={generateRFQ}
              style={{
                width: '100%',
                padding: '12px',
                background: '#3b82f6',
                color: 'white',
                border: 'none',
                borderRadius: '6px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '8px',
                fontWeight: '500',
                fontSize: '15px'
              }}
            >
              <FileText size={18} /> Generate RFQ
            </button>
          </div>
        )}
      </div>
      
      {/* Material Selection Modal */}
      {showMaterialModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(0,0,0,0.5)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000
        }}>
          <div style={{
            background: 'white',
            borderRadius: '8px',
            padding: '24px',
            maxWidth: '600px',
            width: '90%',
            maxHeight: '80vh',
            overflow: 'auto'
          }}>
            <h2 style={{ margin: '0 0 20px 0', fontSize: '20px', fontWeight: '600' }}>Add Material to Takeoff</h2>
            
            <div style={{ marginBottom: '16px' }}>
              <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', fontWeight: '500' }}>
                Select Material
              </label>
              <select
                value={selectedMaterial?.id || ''}
                onChange={(e) => setSelectedMaterial(MOCK_MATERIALS.find(m => m.id === parseInt(e.target.value)))}
                style={{
                  width: '100%',
                  padding: '10px',
                  border: '1px solid #e2e8f0',
                  borderRadius: '6px',
                  fontSize: '14px'
                }}
              >
                <option value="">Choose material...</option>
                {MOCK_MATERIALS.map(material => (
                  <option key={material.id} value={material.id}>
                    {material.partNumber} - {material.description} ({material.size})
                  </option>
                ))}
              </select>
            </div>
            
            <div style={{ marginBottom: '16px' }}>
              <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', fontWeight: '500' }}>
                WBS Category
              </label>
              <select
                value={selectedWBS?.id || ''}
                onChange={(e) => {
                  const findWBS = (categories) => {
                    for (const cat of categories) {
                      if (cat.id === parseInt(e.target.value)) return cat;
                      if (cat.children) {
                        const found = findWBS(cat.children);
                        if (found) return found;
                      }
                    }
                    return null;
                  };
                  setSelectedWBS(findWBS(MOCK_WBS));
                }}
                style={{
                  width: '100%',
                  padding: '10px',
                  border: '1px solid #e2e8f0',
                  borderRadius: '6px',
                  fontSize: '14px'
                }}
              >
                <option value="">Choose WBS...</option>
                {MOCK_WBS[0].children.map(wbs => (
                  <option key={wbs.id} value={wbs.id}>{wbs.name}</option>
                ))}
              </select>
            </div>
            
            <div style={{ marginBottom: '16px' }}>
              <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', fontWeight: '500' }}>
                Quantity {selectedMaterial && `(${selectedMaterial.unit})`}
              </label>
              <input
                type="number"
                value={quantity}
                onChange={(e) => setQuantity(parseFloat(e.target.value) || 0)}
                style={{
                  width: '100%',
                  padding: '10px',
                  border: '1px solid #e2e8f0',
                  borderRadius: '6px',
                  fontSize: '14px'
                }}
                min="0"
                step="0.01"
              />
            </div>
            
            <div style={{ marginBottom: '20px' }}>
              <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', fontWeight: '500' }}>
                Price Multiplier
              </label>
              <input
                type="number"
                value={multiplier}
                onChange={(e) => setMultiplier(parseFloat(e.target.value) || 1)}
                style={{
                  width: '100%',
                  padding: '10px',
                  border: '1px solid #e2e8f0',
                  borderRadius: '6px',
                  fontSize: '14px'
                }}
                min="0"
                step="0.01"
              />
            </div>
            
            {selectedMaterial && (
              <div style={{ background: '#f8fafc', padding: '12px', borderRadius: '6px', marginBottom: '20px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px', fontSize: '14px' }}>
                  <span style={{ color: '#64748b' }}>Extended Price:</span>
                  <strong>${((selectedMaterial.listPrice * quantity * multiplier) || 0).toFixed(2)}</strong>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '14px' }}>
                  <span style={{ color: '#64748b' }}>Extended Labor:</span>
                  <strong>{((selectedMaterial.laborUnits * quantity) || 0).toFixed(2)} hrs</strong>
                </div>
              </div>
            )}
            
            <div style={{ display: 'flex', gap: '12px' }}>
              <button
                onClick={() => {
                  setShowMaterialModal(false);
                  setSelectedMaterial(null);
                  setSelectedWBS(null);
                  setQuantity(0);
                  setMultiplier(1.0);
                }}
                style={{
                  flex: 1,
                  padding: '12px',
                  background: 'white',
                  border: '1px solid #e2e8f0',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  fontWeight: '500'
                }}
              >
                Cancel
              </button>
              <button
                onClick={saveTakeoffItem}
                style={{
                  flex: 1,
                  padding: '12px',
                  background: '#3b82f6',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  fontWeight: '500'
                }}
              >
                Add to Takeoff
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TakeoffMeasurementUI;