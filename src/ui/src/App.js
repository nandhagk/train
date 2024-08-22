import React, { useState } from 'react';
import './App.css';
import { FaEdit, FaSave, FaPlus } from 'react-icons/fa';

function App() {
  const [rows, setRows] = useState([]);
  const [editingRowIndex, setEditingRowIndex] = useState(null);

  const addRow = () => {
    setRows([...rows, { column1: '', column2: '', column3: '', isEditing: true }]);
    setEditingRowIndex(rows.length);
  };

  const handleInputChange = (e, index, field) => {
    const newRows = rows.map((row, i) =>
      i === index ? { ...row, [field]: e.target.value } : row
    );
    setRows(newRows);
  };

  const saveRow = (index) => {
    const newRows = rows.map((row, i) =>
      i === index ? { ...row, isEditing: false } : row
    );
    setRows(newRows);
    setEditingRowIndex(null);
  };

  const editRow = (index) => {
    setEditingRowIndex(index);
    const newRows = rows.map((row, i) =>
      i === index ? { ...row, isEditing: true } : row
    );
    setRows(newRows);
  };

  return (
    <div className="app-container">
      <h1>ftcbbbbbbbbbbbbbbbbbbb</h1>
      <button className="add-row-button" onClick={addRow}>
        <FaPlus /> Add Row
      </button>
      <table className="styled-table">
        <thead>
          <tr>
            <th>Column 1</th>
            <th>Column 2</th>
            <th>Column 3</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr key={index}>
              {row.isEditing ? (
                <>
                  <td>
                    <input
                      type="text"
                      value={row.column1}
                      onChange={(e) => handleInputChange(e, index, 'column1')}
                      className="table-input"
                    />
                  </td>
                  <td>
                    <input
                      type="text"
                      value={row.column2}
                      onChange={(e) => handleInputChange(e, index, 'column2')}
                      className="table-input"
                    />
                  </td>
                  <td>
                    <input
                      type="text"
                      value={row.column3}
                      onChange={(e) => handleInputChange(e, index, 'column3')}
                      className="table-input"
                    />
                  </td>
                  <td>
                    <button className="save-button" onClick={() => saveRow(index)}>
                      <FaSave /> Save
                    </button>
                  </td>
                </>
              ) : (
                <>
                  <td>{row.column1}</td>
                  <td>{row.column2}</td>
                  <td>{row.column3}</td>
                  <td>
                    <button className="edit-button" onClick={() => editRow(index)}>
                      <FaEdit /> Edit
                    </button>
                  </td>
                </>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default App;
