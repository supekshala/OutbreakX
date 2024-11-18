import React, { useState, useEffect, useRef } from 'react';
import { MapContainer, TileLayer, Marker, useMapEvents } from 'react-leaflet';
import L from 'leaflet';
import axios from 'axios';
import 'leaflet/dist/leaflet.css';

interface MarkerData {
  location: {
    type: string;
    coordinates: [number, number];
  };
  description: string;
}

const icon = new L.Icon({
  iconUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon.png',
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon-2x.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
});

// Interface defining the structure of marker data
// Each marker has a location (with type and coordinates) and a description
interface MarkerData {
  location: {
    type: string;
    coordinates: [number, number];
  };
  description: string;
}

// Define interfaces for our simulation
interface Agent {
  id: number;
  position: [number, number];
  path: [number, number][];
  currentPathIndex: number;
}

interface SimulationState {
  agents: Agent[];
  isRunning: boolean;
}

// Main map component that handles markers and interactions
const MapComponent: React.FC = () => {
  // State for storing markers and right-click position information
  const [markers, setMarkers] = useState<MarkerData[]>([]);
  const [rightClickPos, setRightClickPos] = useState<{
    lat: number;
    lng: number;
    clientX: number;
    clientY: number;
  } | null>(null);
  const [descriptionDialog, setDescriptionDialog] = useState<{
    isOpen: boolean;
    position: { lat: number; lng: number; } | null;
    description: string;
  }>({
    isOpen: false,
    position: null,
    description: ''
  });
  const [simulation, setSimulation] = useState<SimulationState>({
    agents: [],
    isRunning: false
  });
  
  // Animation frame reference
  const animationFrameRef = useRef<number>();
  
  // Helper function to generate random path
  const generateRandomPath = (startPos: [number, number], numPoints: number): [number, number][] => {
    const path: [number, number][] = [startPos];
    let currentPos = startPos;
    
    for (let i = 0; i < numPoints; i++) {
      const newPos: [number, number] = [
        currentPos[0] + (Math.random() - 0.5) * 0.01,
        currentPos[1] + (Math.random() - 0.5) * 0.01
      ];
      path.push(newPos);
      currentPos = newPos;
    }
    
    return path;
  };

  // Initialize simulation
  const initializeSimulation = (numAgents: number = 50) => {
    console.log("Initializing simulation...");
    const newAgents: Agent[] = Array.from({ length: numAgents }, (_, i) => ({
      id: i,
      position: [51.505 + (Math.random() - 0.5) * 0.1, -0.09 + (Math.random() - 0.5) * 0.1],
      path: generateRandomPath([51.505, -0.09], 10),
      currentPathIndex: 0
    }));

    console.log("Created agents:", newAgents);
    setSimulation({
      agents: newAgents,
      isRunning: true
    });
  };

  // Update agent positions
  const updateAgents = () => {
    setSimulation(prev => ({
      ...prev,
      agents: prev.agents.map(agent => {
        const nextPoint = agent.path[agent.currentPathIndex + 1];
        if (!nextPoint) {
          // Reset to beginning of path if we've reached the end
          return { ...agent, currentPathIndex: 0 };
        }

        const speed = 0.1; // Adjust this to control movement speed
        const currentPos = agent.position;
        const dx = (nextPoint[0] - currentPos[0]) * speed;
        const dy = (nextPoint[1] - currentPos[1]) * speed;

        return {
          ...agent,
          position: [currentPos[0] + dx, currentPos[1] + dy],
          currentPathIndex: Math.abs(dx) < 0.0001 && Math.abs(dy) < 0.0001 
            ? agent.currentPathIndex + 1 
            : agent.currentPathIndex
        };
      })
    }));
  };

  // Animation loop
  useEffect(() => {
    console.log("Simulation state changed:", simulation);
  }, [simulation]);

  useEffect(() => {
    if (simulation.isRunning) {
      console.log("Animation started");
      const animate = () => {
        updateAgents();
        animationFrameRef.current = requestAnimationFrame(animate);
      };
      
      animationFrameRef.current = requestAnimationFrame(animate);
      
      return () => {
        console.log("Animation cleanup");
        if (animationFrameRef.current) {
          cancelAnimationFrame(animationFrameRef.current);
        }
      };
    }
  }, [simulation.isRunning]);

  // Add simulation controls
  const simulationControls = (
    <div style={{
      position: 'absolute',
      top: '20px',
      right: '20px',
      zIndex: 1000,
      background: 'white',
      padding: '10px',
      borderRadius: '8px',
      boxShadow: '0 2px 6px rgba(0,0,0,0.3)'
    }}>
      <button
        onClick={() => simulation.isRunning ? setSimulation(prev => ({ ...prev, isRunning: false })) : initializeSimulation()}
        style={{
          padding: '8px 16px',
          background: simulation.isRunning ? '#e74c3c' : '#2ecc71',
          color: 'white',
          border: 'none',
          borderRadius: '4px',
          cursor: 'pointer'
        }}
      >
        {simulation.isRunning ? 'Stop Simulation' : 'Start Simulation'}
      </button>
    </div>
  );

  // Component to handle map events (click and right-click)
  const MapEventHandler = () => {
    useMapEvents({
      // Left click - Add marker with user-provided description
      click: (e) => {
        const { lat, lng } = e.latlng;
        setDescriptionDialog({
          isOpen: true,
          position: { lat, lng },
          description: ''
        });
      },
      // Right click - Show coordinates in a popup overlay
      contextmenu: (e) => {
        const { lat, lng } = e.latlng;
        setRightClickPos({ 
          lat, 
          lng, 
          clientX: e.originalEvent.clientX,
          clientY: e.originalEvent.clientY
        });
        e.originalEvent.preventDefault();
      }
    });
    return null;
  };

  // Add function to handle marker creation
  const handleCreateMarker = () => {
    if (descriptionDialog.position && descriptionDialog.description) {
      const newMarker = {
        location: {
          type: 'Point',
          coordinates: [descriptionDialog.position.lng, descriptionDialog.position.lat]
        },
        description: descriptionDialog.description
      };
      
      axios.post('http://localhost:3001/markers', newMarker)
        .then(response => setMarkers([...markers, response.data]))
        .catch(error => console.error('Error creating marker:', error));
      
      setDescriptionDialog({ isOpen: false, position: null, description: '' });
    }
  };

  // Make agents more visible
  const agentIcon = new L.DivIcon({
    className: 'agent-marker',
    html: `<div style="
      width: 16px;
      height: 16px;
      background: red;
      border-radius: 50%;
      opacity: 1;
      border: 2px solid white;
    "></div>`,
    iconSize: [16, 16],
  });

  return (
    <div style={{ position: 'relative' }}>
      <MapContainer center={[51.505, -0.09]} zoom={13} style={{ height: "100vh", width: "100%" }}>
        <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
        
        {simulation.agents.map(agent => {
          console.log("Rendering agent:", agent);
          return (
            <Marker
              key={agent.id}
              position={agent.position}
              icon={agentIcon}
            />
          );
        })}
        
        <MapEventHandler />
      </MapContainer>
      
      {simulationControls}
    </div>
  );
};

// Add styles for agent markers
const styles = `
  .agent-marker {
    background: none;
    border: none;
  }
`;

// Add styles to document
const styleSheet = document.createElement("style");
styleSheet.innerText = styles;
document.head.appendChild(styleSheet);

export default MapComponent;