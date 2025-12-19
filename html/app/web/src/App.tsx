import { BrowserRouter, Routes, Route } from "react-router-dom";
import MyPage from "./pages/my/index";
import MyPersonasPage from "./pages/my/personas";

// TODO: Add your existing routes here
// This is a placeholder - replace with your actual route configuration

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* TODO: Add your existing routes here */}
        <Route path="/my" element={<MyPage />} />
        <Route path="/my/personas" element={<MyPersonasPage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
