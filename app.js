import React, { useState, useEffect } from 'react';
import Map, { Source, Layer } from 'react-map-gl';
import 'mapbox-gl/dist/mapbox-gl.css';

// Constants for Kochi Heritage Theme
const COLORS = {
  navy: '#1A2744',
  teal: '#008080',
  red: '#D64550',
  grey: '#F4F4F4'
};

const MAPBOX_TOKEN = 'YOUR_MAPBOX_ACCESS_TOKEN'; // Get from mapbox.com

function App() {
  const [selectedWard, setSelectedWard] = useState(null);
  const [aiInsight, setAiInsight] = useState("Select a ward to generate AI policy analysis...");

  // Mock data representing your verified baseline
  const wardData = {
    "Perumanoor": { students: 2354, stRatio: 21.7, smartPct: 85, risk: "High transport density" },
    "Karuvelippady": { students: 1840, stRatio: 32.1, smartPct: 45, risk: "Digital divide gap" }
  };

  const handleMapClick = (e) => {
    const wardName = e.features[0]?.properties.name;
    if (wardName) {
      setSelectedWard(wardName);
      // In production, this would call your Claude API
      setAiInsight(`AI ANALYSIS FOR ${wardName.toUpperCase()}: Critical S:T ratio detected. Recommend shifting 2 teachers from Ward 12 to balance workload.`);
    }
  };

  return (
    <div className="flex h-screen bg-slate-50 font-sans text-slate-900">
      {/* Sidebar */}
      <div className="w-96 bg-white shadow-xl z-10 p-6 flex flex-col border-r border-slate-200">
        <h1 className="text-2xl font-bold text-navy-900 mb-2" style={{color: COLORS.navy}}>KOCHI EDU V2</h1>
        <p className="text-xs text-slate-500 mb-6 uppercase tracking-widest">Intelligence Hub & Policy Engine</p>
        
        {selectedWard ? (
          <div className="space-y-6">
            <div className="bg-teal-50 p-4 rounded-lg border border-teal-100">
              <h2 className="text-xl font-semibold text-teal-800">{selectedWard}</h2>
              <p className="text-sm text-teal-600">Ward Stats Verified ✅</p>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="p-3 bg-slate-100 rounded">
                <p className="text-xs text-slate-500">S:T Ratio</p>
                <p className="text-lg font-bold">{wardData[selectedWard]?.stRatio || '21.7'}</p>
              </div>
              <div className="p-3 bg-slate-100 rounded">
                <p className="text-xs text-slate-500">Smart CL%</p>
                <p className="text-lg font-bold">{wardData[selectedWard]?.smartPct || '67'}%</p>
              </div>
            </div>

            <div className="mt-8">
              <h3 className="text-sm font-bold mb-2 flex items-center">
                <span className="mr-2">🤖</span> CLAUDE AI INSIGHT
              </h3>
              <div className="p-4 bg-navy-900 text-slate-700 italic border-l-4 border-teal-500 rounded text-sm leading-relaxed">
                "{aiInsight}"
              </div>
            </div>
          </div>
        ) : (
          <div className="text-slate-400 text-center mt-20">Click on a ward to begin analysis</div>
        )}
      </div>

      {/* Main Map Area */}
      <div className="flex-1 relative">
        <Map
          initialViewState={{ longitude: 76.2711, latitude: 9.9816, zoom: 12 }}
          style={{ width: '100%', height: '100%' }}
          mapStyle="mapbox://styles/mapbox/light-v10"
          mapboxAccessToken={MAPBOX_TOKEN}
          onClick={handleMapClick}
          interactiveLayerIds={['wards-fill']}
        >
          {/* Ward Data Source - Replace with your GeoJSON */}
          <Source id="kochi-wards" type="geojson" data="/kochi-wards.json">
            <Layer
              id="wards-fill"
              type="fill"
              paint={{
                'fill-color': COLORS.teal,
                'fill-opacity': 0.4,
                'fill-outline-color': '#fff'
              }}
            />
          </Source>
        </Map>
      </div>
    </div>
  );
}

export default App;